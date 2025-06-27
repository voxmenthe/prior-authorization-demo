import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Type, TypeVar, Optional
from .config import get_config, AppConfig

# Define a TypeVar for Pydantic models to help with type hinting
T = TypeVar('T', bound=BaseModel)


def convert_pydantic_to_gemini_schema(pydantic_model: Type[BaseModel]) -> dict:
    """
    Convert Pydantic schema to Gemini-compatible schema by removing additionalProperties.
    
    This function recursively removes the 'additionalProperties' field from Pydantic 
    model schemas to ensure compatibility with Google's Gemini API which explicitly 
    forbids this field.
    """
    schema = pydantic_model.model_json_schema()
    
    def clean_schema(obj):
        """Recursively remove additionalProperties from schema object."""
        if isinstance(obj, dict):
            # Remove additionalProperties if present
            if 'additionalProperties' in obj:
                del obj['additionalProperties']
            # Recursively clean all values
            for value in obj.values():
                clean_schema(value)
        elif isinstance(obj, list):
            # Recursively clean all list items
            for item in obj:
                clean_schema(item)
    
    clean_schema(schema)
    return schema

class LlmClient:
    """
    A client for interacting with the Google Gemini Large Language Models.

    This class encapsulates the configuration and methods for making API calls
    to the Gemini models, handling initialization, and providing structured
    ways to generate content.
    """
    def __init__(self, model_name: Optional[str] = None, config: Optional[AppConfig] = None, verbose: bool = False):
        """
        Initializes the Gemini client.
        
        Args:
            model_name (str, optional): Override the default model from config.
                                       If None, uses config-based model selection.
            config (AppConfig, optional): Configuration object. If None, loads from environment.
            verbose (bool): Enable verbose logging for API calls.
        """
        load_dotenv()
        
        # Load configuration
        if config is None:
            config = get_config()
        self.config = config
        self.verbose = verbose
        
        # Set up models
        if model_name is not None:
            self.model_name = model_name
            # If override model is provided, keep config fallback
            self.fallback_model = config.model_config.fallback_model
        else:
            # Use config-based model selection
            self.model_name = config.model_config.primary_model
            self.fallback_model = config.model_config.fallback_model
        
        # Initialize client
        self.client = genai.Client(api_key=config.api_key)
        
        if self.verbose:
            print(f"🤖 LLM Client initialized:")
            print(f"   Primary: {self.model_name}")
            print(f"   Fallback: {self.fallback_model}")
            print(f"   Timeout: {self.config.timeout_seconds}s")

    def _generate_with_fallback(self, method_name: str, **kwargs):
        """
        Helper method to handle model fallback with proper warning messages.
        
        Args:
            method_name (str): Name of the generation method being called
            **kwargs: Arguments to pass to the generation method
            
        Returns:
            The response from the successful model call
            
        Raises:
            Exception: If both primary and fallback models fail
        """
        import warnings
        
        try:
            # Try primary model first
            if self.verbose:
                prompt_preview = str(kwargs.get('contents', ''))[:100] + "..." if len(str(kwargs.get('contents', ''))) > 100 else str(kwargs.get('contents', ''))
                print(f"🔄 API Call ({method_name}) to {self.model_name}")
                print(f"   Prompt: {prompt_preview}")
            
            import time
            start_time = time.time()
            response = self.client.models.generate_content(model=self.model_name, **kwargs)
            elapsed = time.time() - start_time
            
            if self.verbose:
                print(f"✅ API Call completed in {elapsed:.2f}s")
                if hasattr(response, 'text') and response.text:
                    response_preview = response.text[:80] + "..." if len(response.text) > 80 else response.text
                    print(f"   Response: {response_preview}")
                elif hasattr(response, 'parsed') and response.parsed:
                    print(f"   Structured response: {type(response.parsed).__name__}")
            
            return response
        except Exception as primary_error:
            # Try fallback model
            try:
                warnings.warn(
                    f"⚠️  PRIMARY MODEL FAILURE: {self.model_name} failed in {method_name}() "
                    f"with error: {str(primary_error)}. "
                    f"Falling back to {self.fallback_model}. "
                    f"This indicates a potential model-specific issue that needs investigation.",
                    UserWarning,
                    stacklevel=3
                )
                return self.client.models.generate_content(model=self.fallback_model, **kwargs)
            except Exception as fallback_error:
                raise Exception(
                    f"Both models failed. Primary ({self.model_name}): {str(primary_error)}. "
                    f"Fallback ({self.fallback_model}): {str(fallback_error)}"
                ) from fallback_error

    def generate_text(self, prompt: str, system_instruction: str = None) -> str:
        """
        Generates free-form text based on a given prompt.
        """
        try:
            response = self._generate_with_fallback(
                method_name="generate_text",
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction
                )
            )
            return response.text
        except Exception as e:
            print(f"An error occurred during text generation: {e}")
            raise

    def generate_structured_json(self, prompt: str, response_schema: Type[T], system_instruction: str = None) -> T:
        """
        Generates a JSON object that conforms to a given Pydantic schema.
        Includes fallback handling for Gemini API schema compatibility issues.
        """
        try:
            response = self._generate_with_fallback(
                method_name="generate_structured_json",
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": response_schema,
                    "system_instruction": system_instruction
                }
            )
            if response.parsed:
                return response.parsed
            else:
                raise ValueError(f"Failed to generate valid JSON. Raw text: {response.text}")
        except Exception as e:
            # Check if this is the additionalProperties error
            if "additionalProperties" in str(e):
                print(f"🔧 Schema compatibility issue detected. Attempting fallback to JSON mode: {e}")
                return self._fallback_to_json_mode(prompt, response_schema, system_instruction)
            else:
                print(f"An error occurred during structured JSON generation: {e}")
                raise

    def _fallback_to_json_mode(self, prompt: str, response_schema: Type[T], system_instruction: str = None) -> T:
        """
        Fallback method that uses JSON mode with manual parsing when structured output fails.
        """
        try:
            # Generate the schema description for the prompt
            schema_info = convert_pydantic_to_gemini_schema(response_schema)
            
            enhanced_prompt = f"""
            {prompt}
            
            IMPORTANT: Return your response as valid JSON that matches this exact schema structure:
            {schema_info}
            
            Ensure the JSON is properly formatted and validates against the schema.
            """
            
            # Use basic text generation with JSON instruction
            response_text = self.generate_text(enhanced_prompt, system_instruction)
            
            # Try to parse the JSON response
            import json
            try:
                json_data = json.loads(response_text)
                return response_schema.model_validate(json_data)
            except json.JSONDecodeError:
                # Try to extract JSON from the response if it's wrapped in other text
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    json_data = json.loads(json_match.group())
                    return response_schema.model_validate(json_data)
                else:
                    raise ValueError(f"Could not parse JSON from response: {response_text}")
                    
        except Exception as e:
            print(f"Fallback JSON mode also failed: {e}")
            raise ValueError(f"Both structured output and JSON mode failed. Last error: {e}")

# Example of how to initialize and test the client
if __name__ == '__main__':
    # --- Show configuration info ---
    from .config import ConfigManager
    
    print("=== LLM Client Configuration Test ===")
    print(ConfigManager.get_model_info())
    print()
    
    # --- Define a Pydantic Schema for testing ---
    class DecisionNode(BaseModel):
        node_id: int
        question: str
        is_terminal: bool
        decision_reasoning: str

    # --- Test the client ---
    try:
        client = LlmClient()
        print(f"--- Testing with Environment: {client.config.environment.value} ---")
        print(f"Primary Model: {client.model_name}")
        print(f"Fallback Model: {client.fallback_model}")
        print()
        
        print("--- Testing Basic Text Generation ---")
        text_prompt = "Explain the concept of a decision tree in simple terms."
        generated_text = client.generate_text(text_prompt, system_instruction="You are a helpful AI assistant.")
        print(f"Prompt: {text_prompt}")
        print(f"Response: {generated_text}\n")

        print("--- Testing Structured JSON Generation ---")
        json_prompt = "Create a decision node for a patient with a heart rate over 100 bpm. The node ID is 1."
        system_instruction_json = "You are an expert in creating clinical decision trees. Create a single node."
        decision_node = client.generate_structured_json(json_prompt, DecisionNode, system_instruction_json)
        print(f"Prompt: {json_prompt}")
        print("Response (parsed Pydantic object):")
        print(decision_node)
        print(f"Question from object: {decision_node.question}")

    except (ValueError, Exception) as e:
        print(f"An error occurred during the test run: {e}")
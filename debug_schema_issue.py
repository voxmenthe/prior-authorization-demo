#!/usr/bin/env python3
"""
Focused diagnostic to identify schema-specific issues causing Gemini API hangs.
"""

import time
import json
from pathlib import Path
from src.core.llm_client import LlmClient
from src.core.schemas import ParsedCriteria, DecisionNode, QuestionOrder


def test_schema_complexity():
    """Test if complex nested schemas cause the hanging."""
    print("=== Testing Schema Complexity Issues ===")
    
    client = LlmClient()
    
    # Test 1: Simple schema (known to work)
    print("\n1. Testing simple schema...")
    from pydantic import BaseModel
    
    class SimpleTest(BaseModel):
        name: str
        age: int
    
    try:
        start = time.time()
        response = client.generate_structured_json(
            prompt="Generate a person named John who is 25 years old",
            response_schema=SimpleTest
        )
        elapsed = time.time() - start
        print(f"✅ Simple schema: {elapsed:.2f}s - {response}")
    except Exception as e:
        print(f"❌ Simple schema failed: {e}")
    
    # Test 2: ParsedCriteria schema with minimal content
    print("\n2. Testing ParsedCriteria with minimal content...")
    try:
        start = time.time()
        response = client.generate_structured_json(
            prompt="Parse this simple criterion: Patient must be 18+ years old",
            response_schema=ParsedCriteria
        )
        elapsed = time.time() - start
        print(f"✅ ParsedCriteria minimal: {elapsed:.2f}s - Found {len(response.criteria)} criteria")
    except Exception as e:
        print(f"❌ ParsedCriteria minimal failed: {e}")
    
    # Test 3: ParsedCriteria with complex Jardiance content
    print("\n3. Testing ParsedCriteria with full Jardiance content...")
    jardiance_path = Path("examples/jardiance_criteria.txt")
    with open(jardiance_path, 'r') as f:
        content = f.read()
    
    # Create the exact prompt used in criteria_parser_agent.py
    prompt = f"""
    You are a medical criteria parser. Extract all approval criteria from the following text.
    For each criterion, identify:
    1. The main condition being checked
    2. Whether it's required (ALL) or optional (ANY)
    3. Sub-conditions and their relationships
    4. Specific thresholds, values, or requirements
    5. Exceptions or contraindications

    Text: {content}

    Return a structured JSON that adheres to the provided schema.
    """
    
    try:
        print(f"   Prompt length: {len(prompt)} characters")
        start = time.time()
        response = client.generate_structured_json(
            prompt=prompt,
            response_schema=ParsedCriteria
        )
        elapsed = time.time() - start
        print(f"✅ ParsedCriteria full: {elapsed:.2f}s - Found {len(response.criteria)} criteria")
        
        # Print first criterion for inspection
        if response.criteria:
            first_criterion = response.criteria[0]
            print(f"   First criterion ID: {first_criterion.id}")
            print(f"   First criterion type: {first_criterion.type}")
            
    except Exception as e:
        print(f"❌ ParsedCriteria full failed: {e}")
    
    # Test 4: DecisionNode schema (used in TreeStructureAgent)
    print("\n4. Testing DecisionNode schema...")
    test_criterion = {
        "id": "age_criteria",
        "type": "demographic", 
        "condition": "age >= 18",
        "parameters": {"threshold_value": "18", "threshold_operator": ">=", "unit": "years"}
    }
    
    node_prompt = f"""
    Convert this clinical criterion into a decision tree node question.
    
    Criterion: {json.dumps(test_criterion, indent=2)}
    
    Guidelines:
    1. Make the question clear and unambiguous
    2. Use medical terminology appropriately but include help text
    3. Specify the expected answer format (yes/no, multiple choice, numeric)
    4. Include validation rules for data entry
    
    Return a JSON node structure with id 'n1'.
    """
    
    try:
        print(f"   Node prompt length: {len(node_prompt)} characters")
        start = time.time()
        response = client.generate_structured_json(
            prompt=node_prompt,
            response_schema=DecisionNode
        )
        elapsed = time.time() - start
        print(f"✅ DecisionNode: {elapsed:.2f}s - Node ID: {response.id}")
        print(f"   Question: {response.question[:50]}...")
        
    except Exception as e:
        print(f"❌ DecisionNode failed: {e}")
    
    # Test 5: QuestionOrder schema
    print("\n5. Testing QuestionOrder schema...")
    test_criteria = {
        "CRITERIA": {
            "criteria": [
                {"id": "age", "type": "demographic"},
                {"id": "diabetes", "type": "condition"},
                {"id": "egfr", "type": "lab_value"}
            ]
        }
    }
    
    order_prompt = f"""
    Given these clinical criteria, determine the optimal order for asking questions in a decision tree.
    Consider:
    1. Most exclusionary criteria first (likely to result in denial)
    2. Simple binary questions before complex ones
    3. Logical flow (diagnosis -> age -> prior therapy -> contraindications)
    4. Data collection at the end

    Criteria: {json.dumps(test_criteria, indent=2)}

    Return an ordered list of criterion IDs with reasoning for the order.
    """
    
    try:
        print(f"   Order prompt length: {len(order_prompt)} characters")
        start = time.time()
        response = client.generate_structured_json(
            prompt=order_prompt,
            response_schema=QuestionOrder
        )
        elapsed = time.time() - start
        print(f"✅ QuestionOrder: {elapsed:.2f}s - Order: {response.ordered_ids}")
        print(f"   Reasoning: {response.reasoning[:50]}...")
        
    except Exception as e:
        print(f"❌ QuestionOrder failed: {e}")


def test_prompt_length_impact():
    """Test if very long prompts cause the hanging."""
    print("\n=== Testing Prompt Length Impact ===")
    
    client = LlmClient()
    
    # Create prompts of increasing length
    base_prompt = "Extract criteria from this text: Patient must be 18+ years old."
    
    lengths = [100, 500, 1000, 2000, 5000]
    
    for target_length in lengths:
        # Pad the prompt to target length
        padding = "This is additional context. " * ((target_length - len(base_prompt)) // 25)
        long_prompt = base_prompt + padding
        actual_length = len(long_prompt)
        
        print(f"\nTesting prompt length: {actual_length} characters")
        
        try:
            start = time.time()
            response = client.generate_structured_json(
                prompt=long_prompt,
                response_schema=ParsedCriteria
            )
            elapsed = time.time() - start
            print(f"✅ Length {actual_length}: {elapsed:.2f}s")
            
            if elapsed > 10:  # If it takes more than 10 seconds, flag it
                print(f"⚠️  Long response time detected at {actual_length} characters")
                
        except Exception as e:
            print(f"❌ Length {actual_length} failed: {e}")
            break  # Stop testing longer prompts if we hit an error


def test_different_models_with_complex_schema():
    """Test if certain models handle complex schemas better."""
    print("\n=== Testing Different Models with Complex Schemas ===")
    
    # Test with different models directly
    from google import genai
    import os
    
    models = [
        "gemini-2.5-flash-lite-preview-06-17",  # Fastest
        "gemini-2.5-flash-preview-05-20",       # Default
        "gemini-2.5-pro-preview-06-05"          # Most capable
    ]
    
    # Simple test prompt
    test_prompt = "Extract criteria: Patient must be 18+ and have diabetes"
    
    for model in models:
        print(f"\nTesting model: {model}")
        try:
            client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
            start = time.time()
            
            # Test with structured output
            response = client.models.generate_content(
                model=model,
                contents=test_prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": ParsedCriteria,
                }
            )
            
            elapsed = time.time() - start
            print(f"✅ {model}: {elapsed:.2f}s")
            
            if response.parsed:
                criteria_count = len(response.parsed.criteria) if response.parsed.criteria else 0
                print(f"   Parsed {criteria_count} criteria")
            else:
                print(f"   Raw response length: {len(response.text)}")
                
        except Exception as e:
            print(f"❌ {model} failed: {e}")


def main():
    print("🔍 Schema and Prompt Diagnostic Tests")
    print("=" * 50)
    
    try:
        test_schema_complexity()
        test_prompt_length_impact() 
        test_different_models_with_complex_schema()
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
    
    print("\n" + "=" * 50)
    print("🏁 Diagnostic Complete")


if __name__ == "__main__":
    main()
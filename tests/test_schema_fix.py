#!/usr/bin/env python3
"""Quick test to verify Gemini API schema compatibility fixes."""

import os
from src.core.llm_client import LlmClient, convert_pydantic_to_gemini_schema
from src.core.schemas import DecisionNode, RefinedTreeSection, KeyValuePair

def test_schema_conversion():
    """Test that our schema converter works correctly."""
    
    print("🧪 Testing Schema Converter...")
    
    # Test DecisionNode schema
    print("\n1. Testing DecisionNode schema conversion:")
    original_schema = DecisionNode.model_json_schema()
    cleaned_schema = convert_pydantic_to_gemini_schema(DecisionNode)
    
    print(f"   Original schema has additionalProperties: {'additionalProperties' in str(original_schema)}")
    print(f"   Cleaned schema has additionalProperties: {'additionalProperties' in str(cleaned_schema)}")
    
    # Test RefinedTreeSection schema
    print("\n2. Testing RefinedTreeSection schema conversion:")
    original_refined = RefinedTreeSection.model_json_schema()
    cleaned_refined = convert_pydantic_to_gemini_schema(RefinedTreeSection)
    
    print(f"   Original schema has additionalProperties: {'additionalProperties' in str(original_refined)}")
    print(f"   Cleaned schema has additionalProperties: {'additionalProperties' in str(cleaned_refined)}")

def test_keyvaluepair_conversion():
    """Test KeyValuePair conversion utilities."""
    
    print("\n🔄 Testing KeyValuePair Conversion...")
    
    # Test dict to KeyValuePair conversion
    test_dict = {"validation_type": "required", "max_length": "100"}
    pairs = KeyValuePair.from_dict(test_dict)
    
    print(f"   Original dict: {test_dict}")
    print(f"   Converted to pairs: {[f'{p.key}={p.value}' for p in pairs]}")
    
    # Test back conversion
    back_to_dict = KeyValuePair.to_dict(pairs)
    print(f"   Converted back: {back_to_dict}")
    print(f"   Round-trip successful: {test_dict == back_to_dict}")

def test_real_llm_simple():
    """Test a simple LLM call with our new schema."""
    
    print("\n🚀 Testing Real LLM with Fixed Schema...")
    
    try:
        client = LlmClient()
        
        # Try a simple DecisionNode creation
        prompt = """
        Create a decision node for checking patient age.
        The question should ask if the patient is 18 years or older.
        Include appropriate validation rules.
        """
        
        result = client.generate_structured_json(
            prompt=prompt,
            response_schema=DecisionNode
        )
        
        print(f"   ✅ SUCCESS! Created DecisionNode: {result.question}")
        print(f"   Validation field type: {type(result.validation)}")
        print(f"   Validation content: {result.validation}")
        
        return True
        
    except Exception as e:
        if "additionalProperties" in str(e):
            print(f"   ❌ Still getting additionalProperties error: {e}")
        else:
            print(f"   🔧 Different error (may be expected): {e}")
        return False

if __name__ == "__main__":
    print("🔧 Testing Gemini API Schema Compatibility Fixes")
    print("=" * 50)
    
    test_schema_conversion()
    test_keyvaluepair_conversion()
    
    if os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"):
        test_real_llm_simple()
    else:
        print("\n⚠️  No API key found - skipping real LLM test")
    
    print("\n✅ Schema compatibility test complete!")
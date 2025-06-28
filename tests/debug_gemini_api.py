#!/usr/bin/env python3
"""
Diagnostic script to investigate Gemini API hanging issues.
Tests various scenarios to identify the root cause.
"""

import os
import json
import time
import traceback
from pathlib import Path

from google import genai
from google.genai import types
from dotenv import load_dotenv

from src.core.llm_client import LlmClient
from src.core.schemas import ParsedCriteria, DecisionNode, QuestionOrder
from src.core.config import get_config


def test_basic_api_connection():
    """Test basic API connectivity and authentication."""
    print("=== Testing Basic API Connection ===")
    
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    
    if not api_key:
        print("❌ No GOOGLE_API_KEY found in environment")
        return False
    
    print(f"✅ API Key found (ends with: ...{api_key[-8:]})")
    
    try:
        client = genai.Client(api_key=api_key)
        start_time = time.time()
        
        response = client.models.generate_content(
            model="gemini-2.5-flash-preview-05-20",
            contents="Hello, can you respond with just 'OK'?"
        )
        
        elapsed = time.time() - start_time
        print(f"✅ Basic API call successful in {elapsed:.2f}s: {response.text}")
        return True
        
    except Exception as e:
        print(f"❌ Basic API call failed: {e}")
        print(f"Error type: {type(e).__name__}")
        if hasattr(e, 'code'):
            print(f"Error code: {e.code}")
        if hasattr(e, 'details'):
            print(f"Error details: {e.details}")
        traceback.print_exc()
        return False


def test_structured_json_simple():
    """Test simple structured JSON generation."""
    print("\n=== Testing Simple Structured JSON ===")
    
    try:
        client = LlmClient()
        start_time = time.time()
        
        # Simple schema
        from pydantic import BaseModel
        
        class SimpleResponse(BaseModel):
            message: str
            success: bool
        
        response = client.generate_structured_json(
            prompt="Return a simple success message",
            response_schema=SimpleResponse
        )
        
        elapsed = time.time() - start_time
        print(f"✅ Simple structured JSON successful in {elapsed:.2f}s: {response}")
        return True
        
    except Exception as e:
        print(f"❌ Simple structured JSON failed: {e}")
        print(f"Error type: {type(e).__name__}")
        traceback.print_exc()
        return False


def test_complex_schema():
    """Test with the actual complex schemas used in the demo."""
    print("\n=== Testing Complex Schema (ParsedCriteria) ===")
    
    try:
        client = LlmClient()
        start_time = time.time()
        
        simple_criteria = """
        Patient must be 18+ years old and have diabetes.
        """
        
        response = client.generate_structured_json(
            prompt=f"Parse these criteria: {simple_criteria}",
            response_schema=ParsedCriteria
        )
        
        elapsed = time.time() - start_time
        print(f"✅ Complex schema successful in {elapsed:.2f}s")
        print(f"Response type: {type(response)}")
        print(f"Criteria count: {len(response.criteria) if response.criteria else 0}")
        return True
        
    except Exception as e:
        print(f"❌ Complex schema failed: {e}")
        print(f"Error type: {type(e).__name__}")
        traceback.print_exc()
        return False


def test_jardiance_content():
    """Test with actual Jardiance criteria content."""
    print("\n=== Testing Jardiance Content ===")
    
    try:
        # Read the actual file
        jardiance_path = Path("examples/jardiance_criteria.txt")
        if not jardiance_path.exists():
            print("❌ Jardiance criteria file not found")
            return False
            
        with open(jardiance_path, 'r') as f:
            content = f.read()
        
        print(f"Content length: {len(content)} characters")
        
        client = LlmClient()
        start_time = time.time()
        
        # Test with progressively more complex operations
        print("Testing basic text generation...")
        response1 = client.generate_text(
            prompt=f"Summarize these criteria in one sentence: {content[:500]}..."
        )
        elapsed1 = time.time() - start_time
        print(f"✅ Basic text generation: {elapsed1:.2f}s")
        
        print("Testing structured JSON with Jardiance content...")
        start_time2 = time.time()
        
        response2 = client.generate_structured_json(
            prompt=f"Extract key criteria from: {content}",
            response_schema=ParsedCriteria
        )
        
        elapsed2 = time.time() - start_time2
        print(f"✅ Structured JSON with Jardiance: {elapsed2:.2f}s")
        print(f"Extracted {len(response2.criteria) if response2.criteria else 0} criteria")
        return True
        
    except Exception as e:
        print(f"❌ Jardiance content test failed: {e}")
        print(f"Error type: {type(e).__name__}")
        if hasattr(e, 'response'):
            print(f"HTTP Response: {e.response}")
        traceback.print_exc()
        return False


def test_model_variants():
    """Test different model variants to see if specific model causes issues."""
    print("\n=== Testing Different Model Variants ===")
    
    models_to_test = [
        "gemini-2.5-flash-preview-05-20",
        "gemini-2.5-flash-lite-preview-06-17", 
        "gemini-2.5-pro-preview-06-05"
    ]
    
    for model in models_to_test:
        print(f"\nTesting model: {model}")
        try:
            load_dotenv()
            client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
            start_time = time.time()
            
            response = client.models.generate_content(
                model=model,
                contents="Respond with just 'Working' if you can process this."
            )
            
            elapsed = time.time() - start_time
            print(f"✅ {model}: {elapsed:.2f}s - {response.text}")
            
        except Exception as e:
            print(f"❌ {model}: {e}")
            if hasattr(e, 'code'):
                print(f"  Error code: {e.code}")


def test_timeout_behavior():
    """Test API behavior with intentionally long requests."""
    print("\n=== Testing Timeout Behavior ===")
    
    try:
        client = LlmClient()
        
        # Create a prompt that might take a long time
        long_prompt = """
        Please analyze this very long medical criteria document and extract every single criterion in extreme detail.
        """ + "Repeat this analysis multiple times to be absolutely thorough. " * 100
        
        print("Testing with intentionally long/complex prompt...")
        start_time = time.time()
        
        response = client.generate_text(prompt=long_prompt)
        
        elapsed = time.time() - start_time
        print(f"✅ Long prompt completed in {elapsed:.2f}s")
        print(f"Response length: {len(response)} characters")
        
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ Long prompt failed after {elapsed:.2f}s: {e}")
        print(f"Error type: {type(e).__name__}")


def test_rate_limits():
    """Test if we're hitting rate limits."""
    print("\n=== Testing Rate Limits ===")
    
    try:
        client = LlmClient()
        
        for i in range(5):
            print(f"Request {i+1}/5...")
            start_time = time.time()
            
            response = client.generate_text("Count to 10")
            elapsed = time.time() - start_time
            print(f"  ✅ Request {i+1}: {elapsed:.2f}s")
            
            # Small delay between requests
            time.sleep(0.5)
            
    except Exception as e:
        print(f"❌ Rate limit test failed: {e}")
        if "quota" in str(e).lower() or "rate" in str(e).lower():
            print("🚨 This looks like a rate limiting issue!")


def main():
    """Run all diagnostic tests."""
    print("🔍 Gemini API Diagnostic Tests")
    print("=" * 50)
    
    # Get config info
    try:
        config = get_config()
        print(f"Environment: {config.environment.value}")
        print(f"Primary model: {config.model_config.primary_model}")
        print(f"Timeout: {config.timeout_seconds}s")
        print()
    except Exception as e:
        print(f"⚠️  Config error: {e}")
        print()
    
    tests = [
        test_basic_api_connection,
        test_structured_json_simple,
        test_complex_schema,
        test_model_variants,
        test_jardiance_content,
        test_timeout_behavior,
        test_rate_limits
    ]
    
    results = {}
    
    for test_func in tests:
        try:
            results[test_func.__name__] = test_func()
        except KeyboardInterrupt:
            print(f"\n🛑 Test {test_func.__name__} interrupted by user")
            results[test_func.__name__] = False
            break
        except Exception as e:
            print(f"\n💥 Test {test_func.__name__} crashed: {e}")
            results[test_func.__name__] = False
    
    # Summary
    print("\n" + "=" * 50)
    print("🏁 Test Results Summary")
    print("=" * 50)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}")
    
    passed_count = sum(1 for result in results.values() if result is True)
    total_count = len(results)
    print(f"\nOverall: {passed_count}/{total_count} tests passed")
    
    if passed_count < total_count:
        print("\n🚨 Issues detected! Check the failing tests above for details.")
    else:
        print("\n🎉 All tests passed! The API seems to be working correctly.")


if __name__ == "__main__":
    main()
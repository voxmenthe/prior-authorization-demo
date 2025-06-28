"""JSON utility functions for handling LLM input/output."""
import json
import re
from typing import Any, Union


def sanitize_json_for_prompt(data: Any) -> str:
    """
    Clean JSON for embedding in LLM prompts.
    
    Removes indentation and excessive whitespace to prevent cascading
    indentation issues when LLMs generate responses.
    
    Args:
        data: Python object to convert to JSON
        
    Returns:
        Compact JSON string suitable for LLM prompts
    """
    # Convert to compact JSON string without indentation
    json_str = json.dumps(data, separators=(',', ':'), ensure_ascii=False)
    
    # Remove any excessive whitespace (shouldn't be any, but just in case)
    json_str = re.sub(r'\s+', ' ', json_str)
    
    return json_str


def normalize_json_output(json_data: Union[str, dict]) -> str:
    """
    Normalize JSON output before final save.
    
    Handles both string and dict inputs, cleans up formatting issues,
    and returns consistently formatted JSON.
    
    Args:
        json_data: JSON string or Python dict
        
    Returns:
        Properly formatted JSON string with consistent indentation
    """
    try:
        # If already a dict, just format it
        if isinstance(json_data, dict):
            return json.dumps(json_data, indent=2, ensure_ascii=False)
        
        # Parse and re-serialize to ensure consistent formatting
        data = json.loads(json_data)
        return json.dumps(data, indent=2, ensure_ascii=False)
        
    except json.JSONDecodeError:
        # If parsing fails, try to clean common issues
        if isinstance(json_data, str):
            # Remove excessive tabs and newlines
            cleaned = re.sub(r'[\t\n\r]+', ' ', json_data)
            # Collapse multiple spaces
            cleaned = re.sub(r'\s{2,}', ' ', cleaned)
            # Remove tabs that might be inside string values (common LLM issue)
            cleaned = re.sub(r'"\s*\\t+\s*', '"', cleaned)
            
            try:
                data = json.loads(cleaned)
                return json.dumps(data, indent=2, ensure_ascii=False)
            except json.JSONDecodeError:
                # If still failing, try more aggressive cleaning
                # Remove all control characters
                cleaned = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', json_data)
                data = json.loads(cleaned)
                return json.dumps(data, indent=2, ensure_ascii=False)
        else:
            raise ValueError(f"Cannot normalize non-string, non-dict data: {type(json_data)}")
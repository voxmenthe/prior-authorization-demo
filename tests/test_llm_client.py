import pytest
from pydantic import BaseModel

# Define a simple Pydantic model for testing structured JSON generation
class TestResponseSchema(BaseModel):
    name: str
    age: int
    is_student: bool


def test_generate_text(llm_client):
    """Tests the generate_text method with a simple prompt."""
    prompt = "What is the capital of France?"
    response = llm_client.generate_text(prompt)
    assert "Paris" in response


def test_generate_text_with_system_instruction(llm_client):
    """Tests the generate_text method with a system instruction."""
    prompt = "Tell me about yourself."
    system_instruction = "You are a helpful AI assistant."
    response = llm_client.generate_text(prompt, system_instruction=system_instruction)
    assert "AI assistant" in response or "language model" in response


def test_generate_structured_json(llm_client):
    """Tests the generate_structured_json method with a Pydantic schema."""
    prompt = "Generate a JSON object for a person named Alice, who is 30 years old and is a student."
    response = llm_client.generate_structured_json(prompt, TestResponseSchema)
    
    assert isinstance(response, TestResponseSchema)
    assert response.name == "Alice"
    assert response.age == 30
    assert response.is_student is True


def test_generate_structured_json_with_system_instruction(llm_client):
    """Tests the generate_structured_json method with a system instruction."""
    prompt = "Generate a JSON object for a person named Bob, who is 25 years old and is not a student."
    system_instruction = "Always respond with fictional character data."
    response = llm_client.generate_structured_json(prompt, TestResponseSchema, system_instruction=system_instruction)
    
    assert isinstance(response, TestResponseSchema)
    assert response.name == "Bob"
    assert response.age == 25
    assert response.is_student is False

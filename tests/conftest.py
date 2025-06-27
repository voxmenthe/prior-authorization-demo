import pytest
from src.core.llm_client import LlmClient

@pytest.fixture(scope="session")
def llm_client():
    """Provides a session-scoped LlmClient instance for tests."""
    return LlmClient()

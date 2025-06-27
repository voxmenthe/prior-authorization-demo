import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from src.agents.criteria_parser_agent import CriteriaParserAgent
from src.core.schemas import ParsedCriteria, Criterion, CriterionParameter
from src.core.exceptions import CriteriaParsingError


class TestCriteriaParserAgent:
    
    @patch('src.agents.criteria_parser_agent.LlmClient')
    def test_basic_parsing_success(self, mock_llm_client):
        """Test Case 1: Verify that the agent can correctly parse a simple, well-structured criteria text"""
        
        # Setup mock response - structured JSON representing parsed criteria
        mock_parsed_criteria = ParsedCriteria(
            criteria=[
                Criterion(
                    id="diagnosis",
                    type="required",
                    condition="Member has a confirmed diagnosis of Type 2 Diabetes Mellitus",
                    parameters=CriterionParameter(
                        threshold_value="6.5",
                        threshold_operator=">=",
                        unit="%"
                    )
                ),
                Criterion(
                    id="age",
                    type="required", 
                    condition="Member is ≥ 18 years of age",
                    parameters=CriterionParameter(
                        threshold_value="18",
                        threshold_operator=">=",
                        unit="years"
                    )
                )
            ]
        )
        
        # Mock the LLM client
        mock_client_instance = Mock()
        mock_client_instance.generate_structured_json.return_value = mock_parsed_criteria
        mock_llm_client.return_value = mock_client_instance
        
        # Create agent after mocking
        agent = CriteriaParserAgent()
        
        # Test input from ozempic_criteria.txt
        with open('examples/ozempic_criteria.txt', 'r') as f:
            test_input = f.read()
        
        # Execute the parse method
        result = agent.parse(test_input)
        
        # Assertions
        assert isinstance(result, dict)
        assert "CRITERIA" in result
        assert isinstance(result["CRITERIA"], dict)
        assert "criteria" in result["CRITERIA"]
        assert len(result["CRITERIA"]["criteria"]) == 2
        
        # Verify that the LLM was called with the correct prompt structure
        mock_client_instance.generate_structured_json.assert_called_once()
        call_args = mock_client_instance.generate_structured_json.call_args
        assert call_args[1]['response_schema'] == ParsedCriteria
        assert 'medical criteria parser' in call_args[1]['prompt'].lower()
    
    @patch('src.agents.criteria_parser_agent.LlmClient')
    def test_section_extraction_multiple_sections(self, mock_llm_client):
        """Test Case 2: Test the _extract_sections method with multiple sections"""
        
        # Mock the LLM client (not used in this test but needed for init)
        mock_llm_client.return_value = Mock()
        
        # Create agent
        agent = CriteriaParserAgent()
        
        # Test input with multiple sections
        test_text = """
        I. INDICATIONS
        Ozempic is indicated for type 2 diabetes.
        
        II. CRITERIA FOR INITIAL APPROVAL
        Must meet all criteria:
        1. Diagnosis confirmed
        2. Age >= 18
        
        IV. RENEWAL CRITERIA
        Must demonstrate continued benefit.
        """
        
        # Execute section extraction
        sections = agent._extract_sections(test_text)
        
        # For now, the implementation is simplified and returns the whole text as CRITERIA
        # This test documents the current behavior and can be updated when implementation improves
        assert isinstance(sections, dict)
        assert "CRITERIA" in sections
        assert sections["CRITERIA"] == test_text
    
    @patch('src.agents.criteria_parser_agent.LlmClient')
    def test_malformed_llm_response_handling(self, mock_llm_client):
        """Test Case 3: Ensure the agent handles invalid responses from the LLM gracefully"""
        
        # Setup mock to simulate an error during structured JSON generation
        mock_client_instance = Mock()
        mock_client_instance.generate_structured_json.side_effect = ValueError("Failed to generate valid JSON")
        mock_llm_client.return_value = mock_client_instance
        
        # Create agent
        agent = CriteriaParserAgent()
        
        test_input = "Some medical criteria text"
        
        # Execute and verify that the exception propagates appropriately
        with pytest.raises(CriteriaParsingError, match="Failed to parse criteria section"):
            agent.parse(test_input)
    
    @patch('src.agents.criteria_parser_agent.LlmClient')
    def test_parse_criteria_section_direct(self, mock_llm_client):
        """Test the _parse_criteria_section method directly"""
        
        # Setup mock response
        mock_parsed_criteria = ParsedCriteria(
            criteria=[
                Criterion(
                    id="test_criterion",
                    type="required",
                    condition="Test condition",
                    parameters=CriterionParameter()
                )
            ]
        )
        
        mock_client_instance = Mock()
        mock_client_instance.generate_structured_json.return_value = mock_parsed_criteria
        mock_llm_client.return_value = mock_client_instance
        
        # Create agent
        agent = CriteriaParserAgent()
        
        test_section_text = "Member must have confirmed diagnosis"
        
        # Execute the method
        result = agent._parse_criteria_section(test_section_text)
        
        # Assertions
        assert isinstance(result, dict)
        assert "criteria" in result
        assert len(result["criteria"]) == 1
        assert result["criteria"][0]["id"] == "test_criterion"
        assert result["criteria"][0]["condition"] == "Test condition"
    
    @patch('src.agents.criteria_parser_agent.LlmClient')
    def test_parse_indications_placeholder(self, mock_llm_client):
        """Test the _parse_indications placeholder method"""
        
        # Mock the LLM client
        mock_llm_client.return_value = Mock()
        
        # Create agent
        agent = CriteriaParserAgent()
        
        test_text = "Ozempic is indicated for type 2 diabetes"
        result = agent._parse_indications(test_text)
        
        # Currently returns empty dict - this documents current behavior
        assert isinstance(result, dict)
        assert len(result) == 0


# Integration test that doesn't mock the LLM (requires actual API key)
class TestCriteriaParserAgentIntegration:
    
    @pytest.mark.integration
    def test_real_llm_parsing(self):
        """Integration test with real LLM - requires GOOGLE_API_KEY"""
        
        # Load environment variables
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        # Skip if no API key available
        if not os.getenv("GOOGLE_API_KEY"):
            pytest.skip("No GOOGLE_API_KEY available for integration test")
        
        agent = CriteriaParserAgent()
        
        # Use a simple test case
        test_input = """
        CRITERIA FOR APPROVAL:
        1. Patient must be 18 years or older
        2. Patient must have Type 2 Diabetes diagnosis
        """
        
        try:
            result = agent.parse(test_input)
            
            # Basic assertions for real LLM response
            assert isinstance(result, dict)
            assert "CRITERIA" in result
            print(f"Integration test result: {json.dumps(result, indent=2)}")
            
        except Exception as e:
            pytest.fail(f"Integration test failed with real LLM: {e}")
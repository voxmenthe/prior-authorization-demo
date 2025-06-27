import pytest
import json
from unittest.mock import Mock, patch
from src.agents.tree_structure_agent import TreeStructureAgent
from src.core.schemas import QuestionOrder, DecisionNode, KeyValuePair


class TestTreeStructureAgent:
    
    @patch('src.agents.tree_structure_agent.LlmClient')
    def test_node_creation_from_criterion(self, mock_llm_client):
        """Test Case 1: Verify that a single criterion is correctly converted into a decision tree node"""
        
        # Setup mock response for DecisionNode
        mock_decision_node = DecisionNode(
            id="n1",
            type="question",
            question="Is the patient 18 years or older?",
            data_type="boolean",
            help_text="Patient must be at least 18 years of age to qualify",
            validation=[
                KeyValuePair(key="type", value="boolean"),
                KeyValuePair(key="required", value="true")
            ]
        )
        
        # Mock the LLM client
        mock_client_instance = Mock()
        mock_client_instance.generate_structured_json.return_value = mock_decision_node
        mock_llm_client.return_value = mock_client_instance
        
        # Create agent
        agent = TreeStructureAgent()
        
        # Test input - single criterion
        test_criterion = {
            "id": "age",
            "type": "required",
            "condition": "Member is ≥ 18 years of age",
            "parameters": {
                "threshold_value": "18",
                "threshold_operator": ">=",
                "unit": "years"
            }
        }
        
        # Execute the method
        result = agent._create_node_from_criterion(test_criterion, "n1", False)
        
        # Assertions
        assert isinstance(result, dict)
        assert result["id"] == "n1"
        assert result["type"] == "question"
        assert result["question"] == "Is the patient 18 years or older?"
        assert result["data_type"] == "boolean"
        assert "help_text" in result
        
        # Verify LLM was called correctly
        mock_client_instance.generate_structured_json.assert_called_once()
        call_args = mock_client_instance.generate_structured_json.call_args
        assert call_args[1]['response_schema'] == DecisionNode
        assert 'clinical criterion' in call_args[1]['prompt'].lower()
    
    @patch('src.agents.tree_structure_agent.LlmClient')
    def test_question_ordering(self, mock_llm_client):
        """Test Case 2: Verify the agent can determine a logical question order"""
        
        # Load test fixture
        with open('tests/fixtures/parsed_criteria.json', 'r') as f:
            test_criteria = json.load(f)
        
        # Setup mock response for QuestionOrder
        mock_question_order = QuestionOrder(
            ordered_ids=["clinical_appropriateness", "age", "diagnosis", "prior_therapy", "baseline_documentation"],
            reasoning="Start with exclusionary criteria first, then basic eligibility, followed by complex requirements"
        )
        
        # Mock the LLM client
        mock_client_instance = Mock()
        mock_client_instance.generate_structured_json.return_value = mock_question_order
        mock_llm_client.return_value = mock_client_instance
        
        # Create agent
        agent = TreeStructureAgent()
        
        # Execute the method
        result = agent._determine_question_order(test_criteria)
        
        # Assertions
        assert isinstance(result, list)
        assert len(result) == 5
        assert result[0] == "clinical_appropriateness"  # Should start with exclusionary
        assert "age" in result
        assert "diagnosis" in result
        
        # Verify LLM was called correctly
        mock_client_instance.generate_structured_json.assert_called_once()
        call_args = mock_client_instance.generate_structured_json.call_args
        assert call_args[1]['response_schema'] == QuestionOrder
        assert 'optimal order' in call_args[1]['prompt'].lower()
    
    @patch('src.agents.tree_structure_agent.LlmClient')
    def test_full_tree_creation(self, mock_llm_client):
        """Test Case 3: Test the end-to-end tree creation logic of the agent"""
        
        # Load test fixture
        with open('tests/fixtures/parsed_criteria.json', 'r') as f:
            test_criteria = json.load(f)
        
        # Setup mock responses
        mock_question_order = QuestionOrder(
            ordered_ids=["age", "diagnosis"],
            reasoning="Test ordering"
        )
        
        mock_decision_node_1 = DecisionNode(
            id="n1",
            type="question",
            question="Is the patient 18 years or older?",
            data_type="boolean"
        )
        
        mock_decision_node_2 = DecisionNode(
            id="n2", 
            type="question",
            question="Does the patient have Type 2 Diabetes?",
            data_type="boolean"
        )
        
        # Mock the LLM client - need to return different responses for different calls
        mock_client_instance = Mock()
        mock_client_instance.generate_structured_json.side_effect = [
            mock_question_order,  # First call for ordering
            mock_decision_node_1, # Second call for first node
            mock_decision_node_2  # Third call for second node
        ]
        mock_llm_client.return_value = mock_client_instance
        
        # Create agent
        agent = TreeStructureAgent()
        
        # Execute the method
        result = agent.create_tree(test_criteria)
        
        # Assertions
        assert isinstance(result, dict)
        assert "nodes" in result
        assert isinstance(result["nodes"], list)
        assert len(result["nodes"]) >= 2  # At least the two nodes we created
        
        # Check that nodes have expected structure
        nodes = result["nodes"]
        assert nodes[0]["id"] == "n1"
        assert nodes[1]["id"] == "n2"
        
        # Verify LLM was called multiple times
        assert mock_client_instance.generate_structured_json.call_count >= 3
    
    @patch('src.agents.tree_structure_agent.LlmClient')
    def test_generate_outcome_nodes_placeholder(self, mock_llm_client):
        """Test the _generate_outcome_nodes placeholder method"""
        
        # Mock the LLM client
        mock_llm_client.return_value = Mock()
        
        # Create agent
        agent = TreeStructureAgent()
        
        test_criteria = {"criteria": []}
        result = agent._generate_outcome_nodes(test_criteria)
        
        # Currently returns empty list - this documents current behavior
        assert isinstance(result, list)
        assert len(result) == 0
    
    @patch('src.agents.tree_structure_agent.LlmClient')
    def test_connect_nodes_placeholder(self, mock_llm_client):
        """Test the _connect_nodes placeholder method"""
        
        # Mock the LLM client
        mock_llm_client.return_value = Mock()
        
        # Create agent
        agent = TreeStructureAgent()
        
        test_nodes = [
            {"id": "n1", "type": "question"},
            {"id": "n2", "type": "question"}
        ]
        test_criteria = {"criteria": []}
        
        result = agent._connect_nodes(test_nodes, test_criteria)
        
        # Currently returns simple structure - this documents current behavior
        assert isinstance(result, dict)
        assert "nodes" in result
        assert result["nodes"] == test_nodes
    
    @patch('src.agents.tree_structure_agent.LlmClient')
    def test_create_node_uses_model_dump(self, mock_llm_client):
        """Test that _create_node_from_criterion uses model_dump() correctly"""
        
        # Setup mock response
        mock_decision_node = DecisionNode(
            id="test_node",
            type="question", 
            question="Test question?",
            data_type="boolean"
        )
        
        # Mock the LLM client
        mock_client_instance = Mock()
        mock_client_instance.generate_structured_json.return_value = mock_decision_node
        mock_llm_client.return_value = mock_client_instance
        
        # Create agent
        agent = TreeStructureAgent()
        
        test_criterion = {"id": "test", "condition": "test condition"}
        
        # Execute the method
        result = agent._create_node_from_criterion(test_criterion, "test_node", True)
        
        # Should be a dict, not a Pydantic object
        assert isinstance(result, dict)
        assert result["id"] == "test_node"


# Integration test that doesn't mock the LLM (requires actual API key)
class TestTreeStructureAgentIntegration:
    
    @pytest.mark.integration
    def test_real_llm_tree_creation(self):
        """Integration test with real LLM - requires GOOGLE_API_KEY"""
        
        # Load environment variables
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        # Skip if no API key available
        if not os.getenv("GOOGLE_API_KEY"):
            pytest.skip("No GOOGLE_API_KEY available for integration test")
        
        agent = TreeStructureAgent()
        
        # Use a simple test case
        test_criteria = {
            "criteria": [
                {
                    "id": "age",
                    "type": "required",
                    "condition": "Patient must be 18 or older",
                    "parameters": {"threshold_value": "18", "threshold_operator": ">=", "unit": "years"}
                }
            ]
        }
        
        try:
            result = agent.create_tree(test_criteria)
            
            # Basic assertions for real LLM response
            assert isinstance(result, dict)
            assert "nodes" in result
            print(f"Integration test result: {json.dumps(result, indent=2)}")
            
        except Exception as e:
            pytest.fail(f"Integration test failed with real LLM: {e}")
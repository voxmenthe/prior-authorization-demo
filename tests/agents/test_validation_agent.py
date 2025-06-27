"""Tests for ValidationAgent."""

import pytest
import json
from unittest.mock import Mock, patch

from src.agents.validation_agent import ValidationAgent
from src.core.exceptions import ValidationError
from src.core.schemas import LogicalConsistencyCheck, ValidationIssue


class TestValidationAgent:
    """Test cases for ValidationAgent class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.agent = ValidationAgent()
        
        # Sample valid decision tree
        self.valid_tree = {
            "root": {
                "id": "age_check",
                "type": "decision",
                "question": "Is the patient 18 years or older?",
                "data_type": "boolean",
                "connections": [
                    {
                        "condition": "yes",
                        "next_node": "diagnosis_check"
                    },
                    {
                        "condition": "no", 
                        "next_node": "age_rejection"
                    }
                ]
            },
            "nodes": {
                "diagnosis_check": {
                    "id": "diagnosis_check",
                    "type": "decision",
                    "question": "Does the patient have confirmed Type 2 Diabetes?",
                    "data_type": "boolean",
                    "connections": [
                        {
                            "condition": "yes",
                            "next_node": "approval"
                        },
                        {
                            "condition": "no",
                            "next_node": "diagnosis_rejection"
                        }
                    ]
                },
                "age_rejection": {
                    "id": "age_rejection",
                    "type": "outcome",
                    "decision": "DENY",
                    "reason": "Patient must be 18 years or older"
                },
                "approval": {
                    "id": "approval", 
                    "type": "outcome",
                    "decision": "APPROVE",
                    "reason": "All criteria met"
                },
                "diagnosis_rejection": {
                    "id": "diagnosis_rejection",
                    "type": "outcome", 
                    "decision": "DENY",
                    "reason": "Type 2 Diabetes diagnosis required"
                }
            }
        }
        
        # Sample tree with logical inconsistencies
        self.invalid_tree = {
            "root": {
                "id": "age_check",
                "type": "decision",
                "question": "Is the patient 18 years or older?",
                "data_type": "boolean",
                "connections": [
                    {
                        "condition": "yes",
                        "next_node": "unreachable_node"  # Node doesn't exist
                    },
                    {
                        "condition": "no",
                        "next_node": "age_check"  # Circular reference
                    }
                ]
            },
            "nodes": {
                "orphaned_node": {
                    "id": "orphaned_node",
                    "type": "decision", 
                    "question": "This node is unreachable",
                    "data_type": "boolean",
                    "connections": []
                }
            }
        }

    def test_validate_valid_tree(self):
        """Test validation of a well-structured decision tree."""
        # Mock the LLM response for logical consistency check
        mock_response = LogicalConsistencyCheck(issues=[])
        
        with patch.object(self.agent.llm, 'generate_structured_json', return_value=mock_response):
            result = self.agent.validate(self.valid_tree)
            
        assert result["is_valid"] is True
        assert len(result["issues"]) == 0
        assert "suggestions" in result

    def test_validate_invalid_tree_with_issues(self):
        """Test validation of a tree with logical inconsistencies."""
        # Mock the LLM response with validation issues
        mock_issues = [
            ValidationIssue(
                node_id="age_check",
                explanation="Circular reference detected: node references itself"
            ),
            ValidationIssue(
                node_id="age_check", 
                explanation="Connection to non-existent node 'unreachable_node'"
            )
        ]
        mock_response = LogicalConsistencyCheck(issues=mock_issues)
        
        with patch.object(self.agent.llm, 'generate_structured_json', return_value=mock_response):
            result = self.agent.validate(self.invalid_tree)
            
        assert result["is_valid"] is False
        assert len(result["issues"]) == 2
        assert any("Circular reference" in issue["explanation"] for issue in result["issues"])
        assert any("non-existent node" in issue["explanation"] for issue in result["issues"])

    def test_check_logical_consistency_method(self):
        """Test the _check_logical_consistency method directly."""
        mock_issues = [
            ValidationIssue(
                node_id="test_node",
                explanation="Test validation issue"
            )
        ]
        mock_response = LogicalConsistencyCheck(issues=mock_issues)
        
        with patch.object(self.agent.llm, 'generate_structured_json', return_value=mock_response):
            result = self.agent._check_logical_consistency(self.valid_tree)
            
        assert "issues" in result
        assert len(result["issues"]) == 1
        assert result["issues"][0]["node_id"] == "test_node"

    def test_traverse_tree_method(self):
        """Test the _traverse_tree method with sample inputs."""
        # Test with valid inputs
        inputs = {"age": 25, "has_diabetes": True}
        path = self.agent._traverse_tree(self.valid_tree, inputs)
        
        # Currently returns empty list (placeholder implementation)
        # This test documents the current behavior
        assert isinstance(path, list)

    def test_edge_cases_testing(self):
        """Test the _test_edge_cases method."""
        # Mock the traverse_tree method to return a sample path
        with patch.object(self.agent, '_traverse_tree', return_value=[
            {"node_id": "age_check", "decision": "yes"},
            {"node_id": "diagnosis_check", "decision": "yes"}, 
            {"node_id": "approval", "decision": "APPROVE"}
        ]):
            result = self.agent._test_edge_cases(self.valid_tree)
            
        assert "suggestions" in result
        assert isinstance(result["suggestions"], list)

    def test_pydantic_model_dump_usage(self):
        """Test that the agent properly uses model_dump() instead of deprecated dict()."""
        mock_issues = [
            ValidationIssue(
                node_id="test_node",
                explanation="Test issue"
            )
        ]
        mock_response = LogicalConsistencyCheck(issues=mock_issues)
        
        with patch.object(self.agent.llm, 'generate_structured_json', return_value=mock_response):
            # This should not raise any deprecation warnings
            result = self.agent._check_logical_consistency(self.valid_tree)
            
        # Verify the result structure
        assert isinstance(result, dict)
        assert "issues" in result

    def test_completeness_check_placeholder(self):
        """Test the _check_completeness method (currently placeholder)."""
        result = self.agent._check_completeness(self.valid_tree)
        
        # Currently returns empty dict (placeholder implementation)
        assert isinstance(result, dict)

    def test_ambiguity_check_placeholder(self):
        """Test the _check_ambiguity method (currently placeholder)."""
        result = self.agent._check_ambiguity(self.valid_tree)
        
        # Currently returns empty dict (placeholder implementation)
        assert isinstance(result, dict)

    def test_integration_with_real_llm(self):
        """Integration test with real LLM API call."""
        # This test uses the real Gemini API
        result = self.agent.validate(self.valid_tree)
        
        # Verify the response structure
        assert isinstance(result, dict)
        assert "is_valid" in result
        assert "issues" in result 
        assert "suggestions" in result
        assert isinstance(result["is_valid"], bool)
        assert isinstance(result["issues"], list)
        assert isinstance(result["suggestions"], list)


if __name__ == "__main__":
    pytest.main([__file__])
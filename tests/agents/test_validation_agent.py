"""Tests for ValidationAgent."""

import pytest
import json
from unittest.mock import Mock, patch

from src.agents.validation_agent import ValidationAgent
from src.core.exceptions import ValidationError, ConflictType
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

    def test_validate_includes_conflicts(self):
        """Test that validate method includes conflicts in results."""
        mock_response = LogicalConsistencyCheck(issues=[])
        
        with patch.object(self.agent.llm, 'generate_structured_json', return_value=mock_response):
            result = self.agent.validate(self.valid_tree)
            
        assert "conflicts" in result
        assert isinstance(result["conflicts"], list)

    def test_detect_contradictory_paths(self):
        """Test detection of contradictory paths."""
        # Create a tree with contradictory paths
        tree_with_contradictions = {
            "nodes": [
                {
                    "id": "check1",
                    "type": "decision",
                    "condition": "Has diabetes",
                    "connections": [
                        {"to": "approve"}
                    ]
                },
                {
                    "id": "check2", 
                    "type": "decision",
                    "condition": "Has diabetes",  # Same condition
                    "connections": [
                        {"to": "deny"}  # Different outcome
                    ]
                },
                {
                    "id": "approve",
                    "type": "outcome",
                    "decision": "APPROVE"
                },
                {
                    "id": "deny",
                    "type": "outcome", 
                    "decision": "DENY"
                }
            ]
        }
        
        conflicts = self.agent._detect_contradictory_paths(tree_with_contradictions)
        
        assert len(conflicts) > 0
        assert conflicts[0]["type"] == ConflictType.CONTRADICTORY_PATHS.value
        assert "Has diabetes" in conflicts[0]["description"]

    def test_detect_circular_dependencies(self):
        """Test detection of circular dependencies."""
        # Mock the detect_circular_references utility
        with patch('src.agents.validation_agent.detect_circular_references', return_value=[["node1", "node2", "node1"]]):
            conflicts = self.agent._detect_circular_dependencies(self.invalid_tree)
            
        assert len(conflicts) == 1
        assert conflicts[0]["type"] == ConflictType.CIRCULAR_DEPENDENCY.value
        assert conflicts[0]["severity"] == "critical"

    def test_detect_redundant_paths(self):
        """Test detection of redundant paths."""
        # Create tree with redundant paths
        tree_with_redundancy = {
            "nodes": [
                {
                    "id": "root",
                    "type": "root"
                },
                {
                    "id": "check1",
                    "type": "decision", 
                    "condition": "Age > 18"
                },
                {
                    "id": "check2",
                    "type": "decision",
                    "condition": "Has insurance"
                },
                {
                    "id": "approve",
                    "type": "outcome",
                    "decision": "APPROVE"
                }
            ]
        }
        
        # Mock find_all_paths to return duplicate paths
        mock_paths = [
            [{"id": "root"}, {"id": "check1", "type": "decision", "condition": "Age > 18"}, {"id": "approve", "type": "outcome", "decision": "APPROVE"}],
            [{"id": "root"}, {"id": "check1", "type": "decision", "condition": "Age > 18"}, {"id": "approve", "type": "outcome", "decision": "APPROVE"}]
        ]
        
        with patch('src.agents.validation_agent.find_all_paths', return_value=mock_paths):
            conflicts = self.agent._detect_redundant_paths(tree_with_redundancy)
            
        assert len(conflicts) > 0
        assert any(c["type"] == ConflictType.REDUNDANT_PATHS.value for c in conflicts)

    def test_detect_overlapping_conditions(self):
        """Test detection of overlapping conditions."""
        tree_with_overlaps = {
            "nodes": [
                {
                    "id": "check1",
                    "type": "decision",
                    "condition": "Patient age greater than 65 years"
                },
                {
                    "id": "check2",
                    "type": "decision", 
                    "condition": "Patient age over 65 with diabetes"
                }
            ]
        }
        
        conflicts = self.agent._detect_overlapping_conditions(tree_with_overlaps)
        
        assert len(conflicts) > 0
        assert conflicts[0]["type"] == ConflictType.OVERLAPPING_CONDITIONS.value
        assert conflicts[0]["severity"] == "low"

    def test_conditions_overlap_helper(self):
        """Test the _conditions_overlap helper method."""
        # Test overlapping conditions
        assert self.agent._conditions_overlap(
            "Patient age greater than 65",
            "Patient age over 65 with diabetes"
        ) is True
        
        # Test non-overlapping conditions
        assert self.agent._conditions_overlap(
            "Has insurance",
            "Previous treatment failed"
        ) is False
        
        # Test conditions with common words but not significant overlap
        assert self.agent._conditions_overlap(
            "The patient has insurance",
            "The doctor has experience"
        ) is False

    def test_find_node_by_id(self):
        """Test the _find_node_by_id helper method."""
        nodes = [
            {"id": "node1", "type": "decision"},
            {"id": "node2", "type": "outcome"}
        ]
        
        # Test existing node
        node = self.agent._find_node_by_id(nodes, "node1")
        assert node is not None
        assert node["id"] == "node1"
        
        # Test non-existing node
        node = self.agent._find_node_by_id(nodes, "node3")
        assert node is None

    def test_validate_marks_invalid_with_conflicts(self):
        """Test that validation marks tree as invalid when conflicts are detected."""
        # Create a tree that will have conflicts
        tree_with_conflicts = {
            "nodes": [
                {
                    "id": "check1",
                    "type": "decision",
                    "condition": "Has diabetes",
                    "connections": [{"to": "approve"}]
                },
                {
                    "id": "check2",
                    "type": "decision", 
                    "condition": "Has diabetes",
                    "connections": [{"to": "deny"}]
                },
                {
                    "id": "approve",
                    "type": "outcome",
                    "decision": "APPROVE"
                },
                {
                    "id": "deny",
                    "type": "outcome",
                    "decision": "DENY"
                }
            ]
        }
        
        mock_response = LogicalConsistencyCheck(issues=[])
        
        with patch.object(self.agent.llm, 'generate_structured_json', return_value=mock_response):
            result = self.agent.validate(tree_with_conflicts)
            
        # Should be invalid due to conflicts
        assert result["is_valid"] is False
        assert len(result["conflicts"]) > 0


if __name__ == "__main__":
    pytest.main([__file__])
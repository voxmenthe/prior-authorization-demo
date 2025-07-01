"""Tests for enhanced ValidationAgent functionality."""

import pytest
from unittest.mock import Mock, patch

from src.agents.validation_agent import ValidationAgent
from src.core.schemas import (
    LogicalConsistencyCheck, 
    ValidationIssue,
    CompletenessCheck,
    CompletenessIssue,
    AmbiguityCheck,
    AmbiguityIssue
)


class TestValidationEnhancements:
    """Test cases for enhanced ValidationAgent methods."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.agent = ValidationAgent(verbose=True)
        
        # Sample tree for testing
        self.test_tree = {
            "nodes": {
                "n1": {
                    "id": "n1",
                    "type": "decision",
                    "question": "Is patient age greater than threshold?",
                    "condition": "age > threshold",
                    "connections": {"yes": "n2", "no": "denied_age"}
                },
                "n2": {
                    "id": "n2", 
                    "type": "decision",
                    "question": "Does patient have severe symptoms?",
                    "condition": "severe symptoms",
                    "connections": {"yes": "approved", "no": "n3"}
                },
                "n3": {
                    "id": "n3",
                    "type": "decision",
                    "question": "Has patient tried alternative treatments?",
                    "connections": {"yes": "approved", "no": "denied_alt"}
                },
                "approved": {
                    "id": "approved",
                    "type": "outcome",
                    "decision": "APPROVED"
                },
                "denied_age": {
                    "id": "denied_age",
                    "type": "outcome", 
                    "decision": "DENIED"
                },
                "denied_alt": {
                    "id": "denied_alt",
                    "type": "outcome",
                    "decision": "DENIED"
                }
            },
            "metadata": {
                "start_node_id": "n1",
                "original_criteria": ["age_requirement", "severity_check", "alt_treatment"]
            }
        }
    
    def test_check_completeness_with_issues(self):
        """Test completeness check that finds issues."""
        # Mock LLM response with completeness issues
        mock_issues = [
            CompletenessIssue(
                issue_type="missing_criteria",
                description="Missing evaluation for diabetes diagnosis requirement",
                missing_criteria=["diabetes_diagnosis"],
                affected_nodes=["n1"]
            ),
            CompletenessIssue(
                issue_type="incomplete_pathway",
                description="Path from n2 doesn't evaluate all required conditions",
                affected_nodes=["n2", "n3"]
            )
        ]
        mock_response = CompletenessCheck(issues=mock_issues)
        
        with patch.object(self.agent.llm, 'generate_structured_json', return_value=mock_response):
            result = self.agent._check_completeness(self.test_tree)
        
        assert "issues" in result
        assert len(result["issues"]) == 2
        assert result["issues"][0]["node_id"] == "n1"
        assert "diabetes diagnosis" in result["issues"][0]["explanation"]
    
    def test_check_completeness_no_issues(self):
        """Test completeness check with no issues found."""
        mock_response = CompletenessCheck(issues=[])
        
        with patch.object(self.agent.llm, 'generate_structured_json', return_value=mock_response):
            result = self.agent._check_completeness(self.test_tree)
        
        assert result["issues"] == []
    
    def test_check_ambiguity_with_issues(self):
        """Test ambiguity check that finds vague conditions."""
        mock_issues = [
            AmbiguityIssue(
                node_id="n1",
                ambiguous_text="greater than threshold",
                issue_type="missing_threshold",
                suggestion="Specify exact age threshold (e.g., 'age > 18 years')"
            ),
            AmbiguityIssue(
                node_id="n2",
                ambiguous_text="severe symptoms",
                issue_type="subjective_term", 
                suggestion="Define 'severe' with objective criteria (e.g., specific symptom scores)"
            )
        ]
        mock_response = AmbiguityCheck(issues=mock_issues)
        
        with patch.object(self.agent.llm, 'generate_structured_json', return_value=mock_response):
            result = self.agent._check_ambiguity(self.test_tree)
        
        assert len(result["issues"]) == 2
        assert result["issues"][0]["node_id"] == "n1"
        assert "missing_threshold" in result["issues"][0]["explanation"]
        assert "age > 18 years" in result["issues"][0]["explanation"]
    
    def test_traverse_tree_simple_path(self):
        """Test tree traversal with simple inputs."""
        inputs = {"age": 25, "symptoms": "severe", "tried_alternatives": True}
        
        # Test tree traversal
        path = self.agent._traverse_tree(self.test_tree, inputs)
        
        assert len(path) > 0
        assert path[0]["id"] == "n1"  # Should start at n1
        assert path[-1]["type"] == "outcome"  # Should end at an outcome
    
    def test_traverse_tree_with_numeric_conditions(self):
        """Test tree traversal with numeric condition evaluation."""
        # Create a tree with numeric conditions
        numeric_tree = {
            "nodes": {
                "n1": {
                    "id": "n1",
                    "type": "decision",
                    "question": "Is HbA1c > 9.0?",
                    "connections": [
                        {"condition": "hba1c > 9.0", "to": "n2"},
                        {"condition": "hba1c <= 9.0", "to": "denied"}
                    ]
                },
                "n2": {
                    "id": "n2",
                    "type": "outcome",
                    "decision": "APPROVED"
                },
                "denied": {
                    "id": "denied",
                    "type": "outcome",
                    "decision": "DENIED"
                }
            },
            "metadata": {"start_node_id": "n1"}
        }
        
        # Test with high HbA1c
        inputs_high = {"hba1c": 10.5}
        path = self.agent._traverse_tree(numeric_tree, inputs_high)
        assert len(path) == 2
        assert path[-1]["id"] == "n2"  # Should approve
        
        # Test with low HbA1c
        inputs_low = {"hba1c": 7.5}
        path = self.agent._traverse_tree(numeric_tree, inputs_low)
        assert len(path) == 2
        assert path[-1]["id"] == "denied"  # Should deny
    
    def test_analyze_test_results(self):
        """Test the analyze_test_results method."""
        test_results = [
            {"scenario": "Elderly patient", "path": [{"id": "n1"}, {"id": "approved"}], "outcome": "APPROVED"},
            {"scenario": "Young patient", "path": [], "outcome": "No outcome reached"},
            {"scenario": "Complex case", "path": [{"id": "n1"}], "outcome": "APPROVED"},
            {"scenario": "Standard case", "path": [{"id": "n1"}, {"id": "n2"}, {"id": "approved"}], "outcome": "APPROVED"}
        ]
        
        suggestions = self.agent._analyze_test_results(test_results)
        
        assert len(suggestions) > 0
        assert any("did not reach a clear outcome" in s for s in suggestions)
        assert any("short path" in s.lower() or "few decision points" in s for s in suggestions)
    
    def test_evaluate_condition_boolean(self):
        """Test condition evaluation for boolean values."""
        node = {"id": "test"}
        
        assert self.agent._evaluate_condition("yes", {}, node) is True
        assert self.agent._evaluate_condition("no", {}, node) is False
        assert self.agent._evaluate_condition("true", {}, node) is True
        assert self.agent._evaluate_condition("false", {}, node) is False
    
    def test_evaluate_condition_numeric(self):
        """Test condition evaluation for numeric comparisons."""
        node = {"id": "test"}
        inputs = {"age": 25, "score": 7.5, "count": 10}
        
        # Test various operators
        assert self.agent._evaluate_condition("age > 18", inputs, node) is True
        assert self.agent._evaluate_condition("age < 18", inputs, node) is False
        assert self.agent._evaluate_condition("score >= 7.5", inputs, node) is True
        assert self.agent._evaluate_condition("score <= 8.0", inputs, node) is True
        assert self.agent._evaluate_condition("count == 10", inputs, node) is True
        assert self.agent._evaluate_condition("count = 10", inputs, node) is True
    
    def test_evaluate_node_connections_dict_format(self):
        """Test connection evaluation with dict format."""
        node = {
            "id": "test",
            "connections": {
                "age > 18": "next_node",
                "age <= 18": "denied_node"
            }
        }
        inputs = {"age": 25}
        
        next_node = self.agent._evaluate_node_connections(node, inputs, {})
        assert next_node == "next_node"
    
    def test_evaluate_node_connections_list_format(self):
        """Test connection evaluation with list format."""
        node = {
            "id": "test",
            "connections": [
                {"condition": "age > 18", "to": "next_node"},
                {"condition": "age <= 18", "target_node_id": "denied_node"}
            ]
        }
        inputs = {"age": 15}
        
        next_node = self.agent._evaluate_node_connections(node, inputs, {})
        assert next_node == "denied_node"
    
    def test_completeness_error_handling(self):
        """Test error handling in completeness check."""
        with patch.object(self.agent.llm, 'generate_structured_json', side_effect=Exception("API Error")):
            result = self.agent._check_completeness(self.test_tree)
        
        assert result["issues"] == []
    
    def test_ambiguity_error_handling(self):
        """Test error handling in ambiguity check."""
        with patch.object(self.agent.llm, 'generate_structured_json', side_effect=Exception("API Error")):
            result = self.agent._check_ambiguity(self.test_tree)
        
        assert result["issues"] == []
    
    def test_integration_validate_with_new_checks(self):
        """Test full validation including new completeness and ambiguity checks."""
        # Mock all LLM calls
        mock_logical = LogicalConsistencyCheck(issues=[])
        mock_completeness = CompletenessCheck(issues=[
            CompletenessIssue(
                issue_type="missing_criteria",
                description="Missing diabetes check",
                affected_nodes=["n1"]
            )
        ])
        mock_ambiguity = AmbiguityCheck(issues=[
            AmbiguityIssue(
                node_id="n2",
                ambiguous_text="severe",
                issue_type="subjective_term",
                suggestion="Define severity levels"
            )
        ])
        
        # Set up side effects for multiple calls
        with patch.object(self.agent.llm, 'generate_structured_json') as mock_llm:
            mock_llm.side_effect = [mock_logical, mock_completeness, mock_ambiguity]
            
            result = self.agent.validate(self.test_tree)
        
        # Check that all issues are collected
        assert not result["is_valid"]  # Should be invalid due to issues
        assert len(result["issues"]) == 2  # 1 completeness + 1 ambiguity
        
        # Verify issue content
        issue_texts = [issue["explanation"] for issue in result["issues"]]
        assert any("diabetes" in text for text in issue_texts)
        assert any("severe" in text for text in issue_texts)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
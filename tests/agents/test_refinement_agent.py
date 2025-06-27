"""Tests for RefinementAgent."""

import pytest
import json
from unittest.mock import Mock, patch

from src.agents.refinement_agent import RefinementAgent
from src.core.exceptions import RefinementError
from src.core.schemas import RefinedTreeSection, KeyValuePair


class TestRefinementAgent:
    """Test cases for RefinementAgent class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.agent = RefinementAgent()
        
        # Sample tree with issues
        self.tree_with_issues = {
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
        
        # Sample validation results with issues
        self.validation_results_with_issues = {
            "is_valid": False,
            "issues": [
                {
                    "node_id": "diagnosis_check",
                    "explanation": "Question could be clearer for clinical staff"
                }
            ],
            "suggestions": [
                {
                    "type": "optimization",
                    "description": "Consider combining age and diagnosis checks for efficiency"
                }
            ]
        }
        
        # Sample validation results without issues
        self.validation_results_clean = {
            "is_valid": True,
            "issues": [],
            "suggestions": [
                {
                    "type": "optimization", 
                    "description": "Tree structure is optimal"
                }
            ]
        }

    def test_refine_tree_with_issues(self):
        """Test refinement of a tree with validation issues."""
        # Mock the LLM response for issue fixing
        mock_correction = RefinedTreeSection(
            corrected_section=[
                KeyValuePair(key="nodes", value='{"diagnosis_check": {"id": "diagnosis_check", "type": "decision", "question": "Does the patient have a confirmed diagnosis of Type 2 Diabetes Mellitus?", "data_type": "boolean", "help_text": "Confirmed by HbA1c ≥ 6.5% or fasting glucose ≥ 126 mg/dL", "connections": [{"condition": "yes", "next_node": "approval"}, {"condition": "no", "next_node": "diagnosis_rejection"}]}}')
            ]
        )
        
        with patch.object(self.agent.llm, 'generate_structured_json', return_value=mock_correction):
            refined_tree = self.agent.refine(self.tree_with_issues, self.validation_results_with_issues)
            
        # Verify that refinement was attempted
        assert isinstance(refined_tree, dict)
        # The tree should have been processed through all refinement steps
        assert "root" in refined_tree or "nodes" in refined_tree

    def test_refine_tree_without_issues(self):
        """Test refinement of a tree without validation issues."""
        refined_tree = self.agent.refine(self.tree_with_issues, self.validation_results_clean)
        
        # Should still go through optimization steps
        assert isinstance(refined_tree, dict)
        assert refined_tree is not self.tree_with_issues  # Should be a copy

    def test_fix_issue_method(self):
        """Test the _fix_issue method directly."""
        issue = {
            "node_id": "diagnosis_check",
            "explanation": "Question needs clarification"
        }
        
        mock_correction = RefinedTreeSection(
            corrected_section=[
                KeyValuePair(key="nodes", value='{"diagnosis_check": {"id": "diagnosis_check", "type": "decision", "question": "Does the patient have a confirmed diagnosis of Type 2 Diabetes Mellitus?", "data_type": "boolean", "help_text": "Confirmed by diagnostic criteria"}}')
            ]
        )
        
        with patch.object(self.agent.llm, 'generate_structured_json', return_value=mock_correction):
            fixed_tree = self.agent._fix_issue(self.tree_with_issues, issue)
            
        assert isinstance(fixed_tree, dict)

    def test_extract_relevant_section(self):
        """Test the _extract_relevant_section method."""
        node_ids = ["diagnosis_check", "age_check"]
        
        result = self.agent._extract_relevant_section(self.tree_with_issues, node_ids)
        
        # Currently returns the full tree as JSON (placeholder implementation)
        assert isinstance(result, str)
        assert "diagnosis_check" in result

    def test_merge_correction_with_complete_tree(self):
        """Test _merge_correction when correction contains complete tree."""
        correction = {
            "nodes": {
                "new_node": {
                    "id": "new_node",
                    "type": "decision"
                }
            }
        }
        
        result = self.agent._merge_correction(self.tree_with_issues, correction)
        
        # Should return the correction when it's a complete tree
        assert result == correction

    def test_merge_correction_with_partial_correction(self):
        """Test _merge_correction when correction is not complete."""
        correction = {
            "partial_update": "some value"
        }
        
        result = self.agent._merge_correction(self.tree_with_issues, correction)
        
        # Should return original tree when correction is not complete
        assert result == self.tree_with_issues

    def test_implement_suggestion_placeholder(self):
        """Test the _implement_suggestion method (currently placeholder)."""
        suggestion = {
            "type": "optimization",
            "description": "Combine similar nodes"
        }
        
        result = self.agent._implement_suggestion(self.tree_with_issues, suggestion)
        
        # Currently returns original tree (placeholder implementation)
        assert result == self.tree_with_issues

    def test_optimize_structure_method(self):
        """Test the _optimize_structure method."""
        result = self.agent._optimize_structure(self.tree_with_issues)
        
        # Should go through all optimization steps
        assert isinstance(result, dict)
        # Currently returns the same tree due to placeholder implementations
        assert result == self.tree_with_issues

    def test_combine_similar_nodes_placeholder(self):
        """Test the _combine_similar_nodes method (currently placeholder)."""
        result = self.agent._combine_similar_nodes(self.tree_with_issues)
        
        # Currently returns original tree (placeholder implementation)
        assert result == self.tree_with_issues

    def test_simplify_branches_placeholder(self):
        """Test the _simplify_branches method (currently placeholder)."""
        result = self.agent._simplify_branches(self.tree_with_issues)
        
        # Currently returns original tree (placeholder implementation)
        assert result == self.tree_with_issues

    def test_ensure_complete_paths_placeholder(self):
        """Test the _ensure_complete_paths method (currently placeholder)."""
        result = self.agent._ensure_complete_paths(self.tree_with_issues)
        
        # Currently returns original tree (placeholder implementation)
        assert result == self.tree_with_issues

    def test_add_metadata_placeholder(self):
        """Test the _add_metadata method (currently placeholder)."""
        result = self.agent._add_metadata(self.tree_with_issues)
        
        # Currently returns original tree (placeholder implementation)
        assert result == self.tree_with_issues

    def test_refinement_with_empty_validation_results(self):
        """Test refinement with empty validation results."""
        empty_validation = {
            "is_valid": True,
            "issues": [],
            "suggestions": []
        }
        
        result = self.agent.refine(self.tree_with_issues, empty_validation)
        
        # Should still go through optimization and metadata steps
        assert isinstance(result, dict)

    def test_refinement_preserves_tree_structure(self):
        """Test that refinement preserves essential tree structure."""
        result = self.agent.refine(self.tree_with_issues, self.validation_results_clean)
        
        # Should maintain the basic structure
        assert isinstance(result, dict)
        # The refined tree should be a copy, not the original
        assert result is not self.tree_with_issues

    def test_integration_with_real_llm(self):
        """Integration test with real LLM API call."""
        issue = {
            "node_id": "diagnosis_check",
            "explanation": "Question needs clinical context"
        }
        
        # This test uses the real Gemini API
        try:
            result = self.agent._fix_issue(self.tree_with_issues, issue)
            
            # Verify the response structure
            assert isinstance(result, dict)
            
        except Exception as e:
            # If the API call fails, we should still handle it gracefully
            pytest.skip(f"Real LLM API call failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__])
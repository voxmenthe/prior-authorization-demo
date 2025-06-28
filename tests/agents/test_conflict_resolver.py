"""Tests for ConflictResolver."""

import pytest
from unittest.mock import Mock, patch

from src.agents.conflict_resolver import ConflictResolver
from src.core.exceptions import ConflictType


class TestConflictResolver:
    """Test cases for ConflictResolver class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.resolver = ConflictResolver()
        
        # Sample tree for testing
        self.sample_tree = {
            "nodes": [
                {
                    "id": "node1",
                    "type": "decision",
                    "condition": "Has diabetes",
                    "connections": [{"to": "approve"}]
                },
                {
                    "id": "node2",
                    "type": "decision",
                    "condition": "Has diabetes",
                    "connections": [{"to": "deny"}]
                },
                {
                    "id": "node3",
                    "type": "decision",
                    "connections": [{"to": "node4"}]
                },
                {
                    "id": "node4",
                    "type": "decision",
                    "connections": [{"to": "node3"}]  # Circular
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
        
        # Sample conflicts
        self.sample_conflicts = [
            {
                'type': ConflictType.CONTRADICTORY_PATHS.value,
                'description': 'Condition "Has diabetes" leads to different outcomes',
                'nodes': ['node1', 'node2'],
                'severity': 'high'
            },
            {
                'type': ConflictType.CIRCULAR_DEPENDENCY.value,
                'description': 'Circular dependency detected: node3 -> node4 -> node3',
                'nodes': ['node3', 'node4', 'node3'],
                'severity': 'critical'
            }
        ]

    def test_resolve_conflicts_empty_list(self):
        """Test resolving empty conflict list."""
        result = self.resolver.resolve_conflicts(self.sample_tree, [])
        
        assert result['tree'] == self.sample_tree
        assert len(result['resolutions']) == 0
        assert len(result['unresolved']) == 0

    def test_group_conflicts_by_type(self):
        """Test grouping conflicts by type."""
        grouped = self.resolver._group_conflicts_by_type(self.sample_conflicts)
        
        assert ConflictType.CONTRADICTORY_PATHS.value in grouped
        assert ConflictType.CIRCULAR_DEPENDENCY.value in grouped
        assert len(grouped[ConflictType.CONTRADICTORY_PATHS.value]) == 1
        assert len(grouped[ConflictType.CIRCULAR_DEPENDENCY.value]) == 1

    def test_resolve_contradictory_paths(self):
        """Test resolution of contradictory paths."""
        conflicts = [self.sample_conflicts[0]]
        
        # Mock LLM response
        with patch.object(self.resolver.llm, 'generate_text', return_value="Refine conditions to be mutually exclusive"):
            result = self.resolver._resolve_contradictory_paths(self.sample_tree, conflicts)
            
        assert len(result['resolved']) == 1
        assert len(result['unresolved']) == 0
        assert result['resolved'][0]['action'] == 'Modified conditions to be mutually exclusive'

    def test_resolve_circular_dependencies(self):
        """Test resolution of circular dependencies."""
        conflicts = [self.sample_conflicts[1]]
        
        result = self.resolver._resolve_circular_dependencies(self.sample_tree.copy(), conflicts)
        
        assert len(result['resolved']) == 1
        assert len(result['unresolved']) == 0
        assert 'Broke circular dependency' in result['resolved'][0]['action']
        
        # Verify the circular connection was removed
        modified_tree = result['tree']
        node4 = next(n for n in modified_tree['nodes'] if n['id'] == 'node4')
        assert not any(conn['to'] == 'node3' for conn in node4.get('connections', []))

    def test_resolve_redundant_paths(self):
        """Test resolution of redundant paths."""
        conflict = {
            'type': ConflictType.REDUNDANT_PATHS.value,
            'description': 'Multiple paths with identical conditions',
            'nodes': ['node1', 'node2', 'node3', 'node4'],
            'severity': 'medium'
        }
        
        tree_copy = self.sample_tree.copy()
        result = self.resolver._resolve_redundant_paths(tree_copy, [conflict])
        
        assert len(result['resolved']) == 1
        assert 'Consolidated redundant paths' in result['resolved'][0]['action']
        
        # Check that some nodes were removed
        assert len(result['tree']['nodes']) < len(self.sample_tree['nodes'])

    def test_resolve_overlapping_conditions(self):
        """Test resolution of overlapping conditions."""
        conflict = {
            'type': ConflictType.OVERLAPPING_CONDITIONS.value,
            'description': 'Conditions may overlap',
            'nodes': ['node1', 'node2'],
            'severity': 'low'
        }
        
        # Mock LLM response
        with patch.object(self.resolver.llm, 'generate_text', return_value="Refined conditions"):
            result = self.resolver._resolve_overlapping_conditions(self.sample_tree, [conflict])
            
        assert len(result['resolved']) == 1
        assert 'Refined overlapping conditions' in result['resolved'][0]['action']

    def test_resolve_conflicts_with_multiple_types(self):
        """Test resolving multiple types of conflicts."""
        with patch.object(self.resolver.llm, 'generate_text', return_value="Resolution"):
            result = self.resolver.resolve_conflicts(self.sample_tree.copy(), self.sample_conflicts)
            
        assert len(result['resolutions']) >= 2
        assert isinstance(result['tree'], dict)
        
        # Check that conflicts were processed
        assert any('contradictory' in str(r).lower() for r in result['resolutions'])
        assert any('circular' in str(r).lower() for r in result['resolutions'])

    def test_resolve_conflicts_with_exceptions(self):
        """Test handling of exceptions during conflict resolution."""
        # Create a conflict that will cause an exception
        bad_conflict = {
            'type': ConflictType.CIRCULAR_DEPENDENCY.value,
            'description': 'Test conflict',
            'nodes': [],  # Empty nodes will cause issues
            'severity': 'critical'
        }
        
        result = self.resolver._resolve_circular_dependencies(self.sample_tree, [bad_conflict])
        
        # Should handle exception gracefully
        assert len(result['resolved']) == 0
        assert len(result['unresolved']) == 1

    def test_resolve_unknown_conflict_type(self):
        """Test handling of unknown conflict types."""
        unknown_conflict = {
            'type': 'unknown_type',
            'description': 'Unknown conflict',
            'nodes': ['node1'],
            'severity': 'medium'
        }
        
        result = self.resolver.resolve_conflicts(self.sample_tree, [unknown_conflict])
        
        # Unknown conflicts should go to unresolved
        assert len(result['unresolved']) == 1
        assert result['unresolved'][0]['type'] == 'unknown_type'

    def test_verbose_output(self):
        """Test verbose mode output."""
        resolver = ConflictResolver(verbose=True)
        
        # Should print initialization message
        with patch('builtins.print') as mock_print:
            resolver = ConflictResolver(verbose=True)
            mock_print.assert_called_with("✅ ConflictResolver initialized")
            
        # Should print resolution message
        with patch('builtins.print') as mock_print:
            resolver.resolve_conflicts(self.sample_tree, self.sample_conflicts)
            assert any("Resolving" in str(call) for call in mock_print.call_args_list)

    def test_tree_immutability(self):
        """Test that original tree is not modified."""
        original_tree_copy = self.sample_tree.copy()
        
        self.resolver.resolve_conflicts(self.sample_tree, self.sample_conflicts)
        
        # Original tree should remain unchanged
        assert self.sample_tree == original_tree_copy


if __name__ == "__main__":
    pytest.main([__file__])
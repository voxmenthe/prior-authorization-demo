"""Conflict resolution strategies for decision tree conflicts."""

from typing import Dict, List, Any
from src.core.exceptions import ConflictType
from src.core.llm_client import LlmClient
from src.core.schemas import ConflictResolution, NodeModification


class ConflictResolver:
    """Resolves conflicts detected in decision trees."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.llm = LlmClient(verbose=verbose)
        if verbose:
            print("✅ ConflictResolver initialized")
    
    def resolve_conflicts(self, tree: dict, conflicts: List[Dict]) -> Dict[str, Any]:
        """
        Resolve detected conflicts in the decision tree.
        
        Args:
            tree: The decision tree structure
            conflicts: List of detected conflicts
            
        Returns:
            Dictionary with resolved tree and resolution details
        """
        # Ensure conflicts is a list
        if not isinstance(conflicts, list):
            if self.verbose:
                print(f"   ⚠️  Warning: Expected list for conflicts, got {type(conflicts)}")
            conflicts = []
        
        if not conflicts:
            return {
                'tree': tree,
                'resolutions': [],
                'unresolved': []
            }
        
        if self.verbose:
            print(f"\n🔧 Resolving {len(conflicts)} conflicts...")
        
        resolved_tree = tree.copy()
        resolutions = []
        unresolved = []
        
        # Group conflicts by type for batch resolution
        conflicts_by_type = self._group_conflicts_by_type(conflicts)
        
        for conflict_type, type_conflicts in conflicts_by_type.items():
            if conflict_type == ConflictType.CONTRADICTORY_PATHS.value:
                results = self._resolve_contradictory_paths(resolved_tree, type_conflicts)
            elif conflict_type == ConflictType.CIRCULAR_DEPENDENCY.value:
                results = self._resolve_circular_dependencies(resolved_tree, type_conflicts)
            elif conflict_type == ConflictType.REDUNDANT_PATHS.value:
                results = self._resolve_redundant_paths(resolved_tree, type_conflicts)
            elif conflict_type == ConflictType.OVERLAPPING_CONDITIONS.value:
                results = self._resolve_overlapping_conditions(resolved_tree, type_conflicts)
            else:
                results = {'resolved': [], 'unresolved': type_conflicts, 'tree': resolved_tree}
            
            resolved_tree = results['tree']
            resolutions.extend(results['resolved'])
            unresolved.extend(results['unresolved'])
        
        return {
            'tree': resolved_tree,
            'resolutions': resolutions,
            'unresolved': unresolved
        }
    
    def _group_conflicts_by_type(self, conflicts: List[Dict]) -> Dict[str, List[Dict]]:
        """Group conflicts by their type."""
        grouped = {}
        for conflict in conflicts:
            # Ensure conflict is a dict, not a string
            if isinstance(conflict, str):
                if self.verbose:
                    print(f"   ⚠️  Warning: Expected dict for conflict, got string: {conflict}")
                # Try to create a minimal conflict dict from the string
                conflict = {
                    'type': 'unknown',
                    'description': conflict,
                    'nodes': [],
                    'severity': 'medium'
                }
            elif not isinstance(conflict, dict):
                if self.verbose:
                    print(f"   ⚠️  Warning: Expected dict for conflict, got {type(conflict)}: {conflict}")
                continue
            
            conflict_type = conflict.get('type', 'unknown')
            if conflict_type not in grouped:
                grouped[conflict_type] = []
            grouped[conflict_type].append(conflict)
        return grouped
    
    def _resolve_contradictory_paths(self, tree: dict, conflicts: List[Dict]) -> Dict:
        """Resolve contradictory path conflicts using structured output."""
        resolved = []
        unresolved = []
        
        for conflict in conflicts:
            try:
                # Use structured output for better resolution
                prompt = f"""
                Analyze this contradictory path conflict in a decision tree:
                
                Conflict: {conflict['description']}
                Affected nodes: {conflict['nodes']}
                Tree structure: {tree}
                
                Suggest how to resolve this contradiction by:
                1. Refining the conditions to be mutually exclusive
                2. Adding additional decision nodes if needed
                3. Clarifying the logic
                
                Provide specific modifications to nodes, including:
                - Which nodes need their conditions updated
                - What the new conditions should be
                - Any new nodes that need to be added
                - Connections that need to be removed or added
                
                Focus on making conditions clear and mutually exclusive.
                """
                
                # Use structured JSON generation
                resolution = self.llm.generate_structured_json(
                    prompt=prompt,
                    response_schema=ConflictResolution
                )
                
                # Apply the resolution modifications
                modified_tree = self._apply_modifications(tree, resolution)
                
                resolved.append({
                    'conflict': conflict,
                    'resolution': resolution.model_dump(),
                    'action': resolution.description,
                    'confidence': resolution.confidence_score
                })
                
                # Update tree for next iteration
                tree = modified_tree
                
            except Exception as e:
                if self.verbose:
                    print(f"   Failed to resolve contradictory path: {e}")
                unresolved.append(conflict)
        
        return {
            'tree': tree,
            'resolved': resolved,
            'unresolved': unresolved
        }
    
    def _apply_modifications(self, tree: dict, resolution: ConflictResolution) -> dict:
        """Apply the modifications from a conflict resolution to the tree."""
        modified_tree = tree.copy()
        nodes = modified_tree.get('nodes', {})
        
        # Apply node modifications
        for mod in resolution.modified_nodes:
            if mod.node_id in nodes:
                node = nodes[mod.node_id]
                
                if mod.modification_type == 'update_condition':
                    node['condition'] = mod.new_value
                elif mod.modification_type == 'update_text':
                    node['question'] = mod.new_value
                elif mod.modification_type == 'add_connection':
                    if 'connections' not in node:
                        node['connections'] = {}
                    # Parse connection format: "condition:target_node"
                    if ':' in mod.new_value:
                        condition, target = mod.new_value.split(':', 1)
                        node['connections'][condition] = target
                elif mod.modification_type == 'remove_connection':
                    if 'connections' in node and mod.old_value in node['connections']:
                        del node['connections'][mod.old_value]
        
        # Add new nodes if any
        if resolution.new_nodes:
            for new_node in resolution.new_nodes:
                node_dict = new_node.model_dump()
                nodes[node_dict['id']] = node_dict
        
        # Remove connections if specified
        if resolution.removed_connections:
            for conn_spec in resolution.removed_connections:
                # Format: "from_node:condition"
                if ':' in conn_spec:
                    from_node, condition = conn_spec.split(':', 1)
                    if from_node in nodes and 'connections' in nodes[from_node]:
                        if condition in nodes[from_node]['connections']:
                            del nodes[from_node]['connections'][condition]
        
        return modified_tree
    
    def _resolve_circular_dependencies(self, tree: dict, conflicts: List[Dict]) -> Dict:
        """Resolve circular dependency conflicts."""
        resolved = []
        unresolved = []
        nodes = tree.get('nodes', [])
        
        # Handle both dict and list formats
        if isinstance(nodes, dict):
            nodes_list = list(nodes.values())
        else:
            nodes_list = nodes
        
        for conflict in conflicts:
            try:
                cycle_nodes = conflict.get('nodes', [])
                
                if cycle_nodes and len(cycle_nodes) >= 2:
                    # Break the cycle by removing the connection from the second-to-last to the last node
                    # For cycle [A, B, C, A], we want to remove C -> A
                    if len(cycle_nodes) >= 3 and cycle_nodes[0] == cycle_nodes[-1]:
                        # This is a proper cycle representation
                        from_node_id = cycle_nodes[-2]
                        to_node_id = cycle_nodes[-1]
                    else:
                        # Fallback for other representations
                        from_node_id = cycle_nodes[-1]
                        to_node_id = cycle_nodes[0]
                    
                    # Find and remove the connection creating the cycle
                    for i, node in enumerate(nodes_list):
                        if node.get('id') == from_node_id:
                            connections = node.get('connections', [])
                            node['connections'] = [
                                conn for conn in connections 
                                if conn.get('to') != to_node_id
                            ]
                            
                            # Update the original structure
                            if isinstance(nodes, dict):
                                nodes[from_node_id] = node
                            else:
                                nodes[i] = node
                            
                            resolved.append({
                                'conflict': conflict,
                                'resolution': f'Removed circular connection from {from_node_id} to {to_node_id}',
                                'action': 'Broke circular dependency'
                            })
                            break
                else:
                    # No cycle nodes provided
                    unresolved.append(conflict)
                
            except Exception as e:
                if self.verbose:
                    print(f"   Failed to resolve circular dependency: {e}")
                unresolved.append(conflict)
        
        return {
            'tree': tree,
            'resolved': resolved,
            'unresolved': unresolved
        }
    
    def _resolve_redundant_paths(self, tree: dict, conflicts: List[Dict]) -> Dict:
        """Resolve redundant path conflicts."""
        resolved = []
        unresolved = []
        nodes = tree.get('nodes', [])
        
        # Handle both dict and list formats
        if isinstance(nodes, dict):
            nodes_list = list(nodes.values())
        else:
            nodes_list = nodes
        
        for conflict in conflicts:
            try:
                redundant_nodes = conflict.get('nodes', [])
                
                if len(redundant_nodes) > 1:
                    # Keep the first path, remove redundant ones
                    nodes_to_remove = set(redundant_nodes[len(redundant_nodes)//2:])
                    
                    # Remove redundant nodes
                    tree['nodes'] = [n for n in nodes if n.get('id') not in nodes_to_remove]
                    
                    # Update connections to skip removed nodes
                    for node in tree['nodes']:
                        if 'connections' in node:
                            node['connections'] = [
                                conn for conn in node['connections']
                                if conn.get('to') not in nodes_to_remove
                            ]
                    
                    resolved.append({
                        'conflict': conflict,
                        'resolution': f'Removed redundant nodes: {list(nodes_to_remove)}',
                        'action': 'Consolidated redundant paths'
                    })
                
            except Exception as e:
                if self.verbose:
                    print(f"   Failed to resolve redundant paths: {e}")
                unresolved.append(conflict)
        
        return {
            'tree': tree,
            'resolved': resolved,
            'unresolved': unresolved
        }
    
    def _resolve_overlapping_conditions(self, tree: dict, conflicts: List[Dict]) -> Dict:
        """Resolve overlapping condition conflicts."""
        resolved = []
        unresolved = []
        
        for conflict in conflicts:
            try:
                # Use LLM to refine overlapping conditions
                prompt = f"""
                Analyze these overlapping conditions in a decision tree:
                
                Conflict: {conflict['description']}
                Affected nodes: {conflict['nodes']}
                
                Suggest how to refine these conditions to be:
                1. Mutually exclusive
                2. Clear and unambiguous
                3. Cover all cases without overlap
                
                Return specific rewording for each condition.
                """
                
                resolution = self.llm.generate_text(prompt)
                
                # For now, just log the resolution
                resolved.append({
                    'conflict': conflict,
                    'resolution': resolution,
                    'action': 'Refined overlapping conditions'
                })
                
            except Exception as e:
                if self.verbose:
                    print(f"   Failed to resolve overlapping conditions: {e}")
                unresolved.append(conflict)
        
        return {
            'tree': tree,
            'resolved': resolved,
            'unresolved': unresolved
        }
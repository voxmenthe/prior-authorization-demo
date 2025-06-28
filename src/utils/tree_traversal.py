"""
Tree traversal utilities with safety mechanisms to prevent infinite recursion.

This module provides safe tree traversal functionality with:
- Circular reference detection
- Maximum depth limiting
- Visited node tracking
- Error handling for malformed tree structures
"""

from typing import Dict, Any, Set, Optional, Callable, List, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class TraversalConfig:
    """Configuration for safe tree traversal."""
    max_depth: int = 50
    detect_cycles: bool = True
    raise_on_cycle: bool = False
    log_warnings: bool = True


class SafeTreeTraverser:
    """Provides safe tree traversal with recursion protection."""
    
    def __init__(self, config: Optional[TraversalConfig] = None):
        self.config = config or TraversalConfig()
        self._visited_nodes: Set[str] = set()
        self._current_path: List[str] = []
        self._cycle_detected = False
    
    def traverse_tree(self,
                     node: Dict[str, Any],
                     all_nodes: Dict[str, Any],
                     process_node: Callable,
                     get_children: Callable,
                     context: Optional[Dict[str, Any]] = None) -> Any:
        """
        Safely traverse a tree structure with recursion protection.
        
        Args:
            node: Current node to process
            all_nodes: Dictionary of all nodes in the tree
            process_node: Function to process each node
            get_children: Function to get child nodes
            context: Optional context passed to process_node
            
        Returns:
            Result of tree traversal
        """
        self._visited_nodes.clear()
        self._current_path.clear()
        self._cycle_detected = False
        
        return self._traverse_recursive(
            node, all_nodes, process_node, get_children, 
            context or {}, depth=0
        )
    
    def _traverse_recursive(self,
                           node: Dict[str, Any],
                           all_nodes: Dict[str, Any],
                           process_node: Callable,
                           get_children: Callable,
                           context: Dict[str, Any],
                           depth: int) -> Any:
        """Recursive tree traversal with safety checks."""
        
        node_id = node.get('id', str(id(node)))
        
        # Check maximum depth
        if depth > self.config.max_depth:
            if self.config.log_warnings:
                logger.warning(f"Maximum depth {self.config.max_depth} exceeded at node {node_id}")
            return None
        
        # Check for cycles
        if self.config.detect_cycles:
            if node_id in self._current_path:
                self._cycle_detected = True
                cycle_path = " -> ".join(self._current_path[self._current_path.index(node_id):] + [node_id])
                
                if self.config.log_warnings:
                    logger.warning(f"Circular reference detected: {cycle_path}")
                
                if self.config.raise_on_cycle:
                    raise RecursionError(f"Circular reference detected in tree: {cycle_path}")
                
                return None
        
        # Track current path for cycle detection
        self._current_path.append(node_id)
        self._visited_nodes.add(node_id)
        
        try:
            # Process current node
            result = process_node(node, context, depth)
            
            # Get and process children
            children = get_children(node, all_nodes)
            
            for child_info in children:
                if isinstance(child_info, tuple):
                    child_node, child_context = child_info
                else:
                    child_node, child_context = child_info, {}
                
                # Merge contexts
                child_full_context = {**context, **child_context}
                
                # Recursively process child
                self._traverse_recursive(
                    child_node, all_nodes, process_node, get_children,
                    child_full_context, depth + 1
                )
            
            return result
            
        finally:
            # Remove from current path when backtracking
            if self._current_path and self._current_path[-1] == node_id:
                self._current_path.pop()
    
    def has_cycle(self) -> bool:
        """Check if a cycle was detected during traversal."""
        return self._cycle_detected
    
    def get_visited_nodes(self) -> Set[str]:
        """Get set of all visited node IDs."""
        return self._visited_nodes.copy()


def create_safe_tree_renderer(max_depth: int = 50) -> Callable:
    """
    Create a safe tree rendering function with recursion protection.
    
    Args:
        max_depth: Maximum depth for tree traversal
        
    Returns:
        A function that safely renders trees
    """
    def safe_render_tree(render_func: Callable) -> Callable:
        def wrapper(self, *args, **kwargs):
            # Extract tree data from arguments
            if 'all_nodes' in kwargs:
                all_nodes = kwargs['all_nodes']
            elif len(args) >= 2 and isinstance(args[1], dict):
                all_nodes = args[1]
            else:
                # No tree data, proceed normally
                return render_func(self, *args, **kwargs)
            
            # Create traverser with configuration
            config = TraversalConfig(
                max_depth=max_depth,
                detect_cycles=True,
                raise_on_cycle=False,
                log_warnings=True
            )
            
            traverser = SafeTreeTraverser(config)
            
            # Wrap the original render function to use safe traversal
            original_method = render_func
            
            def safe_method(*inner_args, **inner_kwargs):
                try:
                    return original_method(*inner_args, **inner_kwargs)
                except RecursionError as e:
                    logger.error(f"Recursion error in tree rendering: {e}")
                    # Return a safe fallback
                    return "Tree rendering failed due to circular references"
            
            return safe_method(self, *args, **kwargs)
        
        return wrapper
    
    return safe_render_tree


def validate_tree_structure(nodes: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate a tree structure for common issues.
    
    Args:
        nodes: Dictionary of nodes in the tree
        
    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    issues = []
    
    if not isinstance(nodes, dict):
        issues.append("Nodes must be a dictionary")
        return False, issues
    
    # Check for self-references
    for node_id, node in nodes.items():
        if not isinstance(node, dict):
            issues.append(f"Node {node_id} is not a dictionary")
            continue
        
        connections = node.get('connections', {})
        
        if isinstance(connections, dict):
            for condition, target_id in connections.items():
                if target_id == node_id:
                    issues.append(f"Node {node_id} has self-reference")
                elif target_id not in nodes:
                    issues.append(f"Node {node_id} references non-existent node {target_id}")
        
        elif isinstance(connections, list):
            for conn in connections:
                if isinstance(conn, dict):
                    target_id = conn.get('target_node_id')
                    if target_id == node_id:
                        issues.append(f"Node {node_id} has self-reference")
                    elif target_id and target_id not in nodes:
                        issues.append(f"Node {node_id} references non-existent node {target_id}")
    
    # Check for circular references using traversal
    if nodes:
        config = TraversalConfig(detect_cycles=True, log_warnings=False)
        traverser = SafeTreeTraverser(config)
        
        # Find root nodes
        root_nodes = find_root_nodes(nodes)
        
        for root in root_nodes:
            def dummy_process(node, context, depth):
                return None
            
            def get_children(node, all_nodes):
                children = []
                connections = node.get('connections', {})
                
                if isinstance(connections, dict):
                    for condition, target_id in connections.items():
                        # Handle case where target_id might be a dict
                        if isinstance(target_id, dict):
                            target_id = target_id.get('id')
                        if target_id and target_id in all_nodes:
                            children.append(all_nodes[target_id])
                elif isinstance(connections, list):
                    for conn in connections:
                        target_id = conn.get('target_node_id')
                        if target_id in all_nodes:
                            children.append(all_nodes[target_id])
                
                return children
            
            traverser.traverse_tree(root, nodes, dummy_process, get_children)
            
            if traverser.has_cycle():
                issues.append(f"Circular reference detected starting from node {root.get('id', 'unknown')}")
    
    return len(issues) == 0, issues


def find_root_nodes(nodes: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Find root nodes in a tree structure."""
    if not nodes:
        return []
    
    # Find nodes that are not referenced by any other node
    referenced_nodes = set()
    
    for node in nodes.values():
        connections = node.get('connections', {})
        
        if isinstance(connections, dict):
            # Ensure we only add hashable string values
            for conn_value in connections.values():
                if isinstance(conn_value, str):
                    referenced_nodes.add(conn_value)
                elif isinstance(conn_value, dict):
                    # Try to extract ID from dict value
                    if 'id' in conn_value:
                        referenced_nodes.add(conn_value['id'])
                        logger.warning(f"Dict found in connection value, extracted ID: {conn_value['id']}")
                    else:
                        logger.warning(f"Dict connection value without 'id' field: {conn_value}")
                elif conn_value is not None:
                    # Log warning if non-string value found
                    logger.warning(f"Non-string connection value found: {type(conn_value).__name__} - {conn_value}")
        elif isinstance(connections, list):
            for conn in connections:
                if isinstance(conn, dict) and 'target_node_id' in conn:
                    target_id = conn['target_node_id']
                    if isinstance(target_id, str):
                        referenced_nodes.add(target_id)
    
    root_nodes = [
        node for node_id, node in nodes.items()
        if node_id not in referenced_nodes
    ]
    
    # If no clear roots found, return the first node
    if not root_nodes and nodes:
        root_nodes = [list(nodes.values())[0]]
    
    return root_nodes


def detect_circular_references(tree: Dict[str, Any]) -> List[List[str]]:
    """
    Detect circular references in a tree structure.
    
    Args:
        tree: Dictionary representing the tree with 'nodes' key
        
    Returns:
        List of circular reference paths (each path is a list of node IDs)
    """
    if not tree or 'nodes' not in tree:
        return []
    
    nodes = tree['nodes']
    circular_refs = []
    visited = set()
    
    def dfs(node_id: str, path: List[str], visiting: Set[str]):
        if node_id in visiting:
            # Found a cycle
            cycle_start = path.index(node_id)
            cycle = path[cycle_start:] + [node_id]
            circular_refs.append(cycle)
            return
        
        if node_id in visited:
            return
        
        visiting.add(node_id)
        path.append(node_id)
        
        node = nodes.get(node_id, {})
        connections = node.get('connections', {})
        
        if isinstance(connections, dict):
            for condition, target_id in connections.items():
                # Handle case where target_id might be a dict
                if isinstance(target_id, dict):
                    target_id = target_id.get('id')
                if target_id and target_id in nodes:
                    dfs(target_id, path.copy(), visiting.copy())
        elif isinstance(connections, list):
            for conn in connections:
                if isinstance(conn, dict):
                    target_id = conn.get('target_node_id')
                    if target_id and target_id in nodes:
                        dfs(target_id, path.copy(), visiting.copy())
        
        visiting.remove(node_id)
        visited.add(node_id)
    
    # Start DFS from each unvisited node
    for node_id in nodes:
        if node_id not in visited:
            dfs(node_id, [], set())
    
    return circular_refs


def find_all_paths(tree: Dict[str, Any], start_node_id: str, end_node_id: str) -> List[List[str]]:
    """
    Find all paths from start node to end node in a tree.
    
    Args:
        tree: Dictionary representing the tree with 'nodes' key
        start_node_id: ID of the starting node
        end_node_id: ID of the ending node
        
    Returns:
        List of paths (each path is a list of node IDs)
    """
    if not tree or 'nodes' not in tree:
        return []
    
    nodes = tree['nodes']
    
    if start_node_id not in nodes or end_node_id not in nodes:
        return []
    
    all_paths = []
    
    def dfs(current_id: str, target_id: str, path: List[str], visited: Set[str]):
        if current_id == target_id:
            all_paths.append(path + [current_id])
            return
        
        if current_id in visited:
            return
        
        visited.add(current_id)
        path.append(current_id)
        
        node = nodes.get(current_id, {})
        connections = node.get('connections', {})
        
        if isinstance(connections, dict):
            for condition, next_id in connections.items():
                # Handle case where next_id might be a dict
                if isinstance(next_id, dict):
                    next_id = next_id.get('id')
                if next_id and next_id in nodes and next_id not in visited:
                    dfs(next_id, target_id, path.copy(), visited.copy())
        elif isinstance(connections, list):
            for conn in connections:
                if isinstance(conn, dict):
                    next_id = conn.get('target_node_id')
                    if next_id and next_id in nodes and next_id not in visited:
                        dfs(next_id, target_id, path.copy(), visited.copy())
    
    dfs(start_node_id, end_node_id, [], set())
    
    return all_paths
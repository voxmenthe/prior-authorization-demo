from typing import List, Dict, Set, Tuple
from src.core.llm_client import LlmClient
from src.core.schemas import LogicalConsistencyCheck
from src.core.exceptions import ConflictType
from src.utils.tree_traversal import find_all_paths, detect_circular_references
from src.utils.json_utils import sanitize_json_for_prompt

class ValidationAgent:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.llm = LlmClient(verbose=verbose)
        if verbose:
            print("✅ ValidationAgent initialized")
        
    def validate(self, tree: dict) -> dict:
        if self.verbose:
            print(f"\n🔍 Validating tree structure")
        
        validation_results = {
            "is_valid": True,
            "issues": [],
            "suggestions": [],
            "conflicts": []  # New field for conflicts
        }
        
        if self.verbose:
            node_count = len(tree.get('nodes', [])) if isinstance(tree, dict) else 0
            print(f"   Checking {node_count} nodes for logical consistency...")
        
        # Check for logical consistency
        logic_check = self._check_logical_consistency(tree)
        validation_results["issues"].extend(logic_check.get("issues", []))
        
        # Check for specific conflicts
        conflicts = []
        
        # Detect contradictory paths
        contradictory = self._detect_contradictory_paths(tree)
        conflicts.extend(contradictory)
        
        # Detect circular dependencies
        circular = self._detect_circular_dependencies(tree)
        conflicts.extend(circular)
        
        # Detect redundant paths
        redundant = self._detect_redundant_paths(tree)
        conflicts.extend(redundant)
        
        # Detect overlapping conditions
        overlapping = self._detect_overlapping_conditions(tree)
        conflicts.extend(overlapping)
        
        validation_results["conflicts"] = conflicts
        
        # Check for completeness
        completeness_check = self._check_completeness(tree)
        validation_results["issues"].extend(completeness_check.get("issues", []))
        
        # Check for ambiguity
        ambiguity_check = self._check_ambiguity(tree)
        validation_results["issues"].extend(ambiguity_check.get("issues", []))
        
        # Simulate edge cases
        edge_case_results = self._test_edge_cases(tree)
        validation_results["suggestions"].extend(edge_case_results.get("suggestions", []))
        
        validation_results["is_valid"] = len(validation_results["issues"]) == 0 and len(conflicts) == 0
        
        return validation_results
    
    def _check_logical_consistency(self, tree: dict) -> dict:
        prompt = f"""
        Analyze this decision tree for logical inconsistencies:
        
        Tree: {sanitize_json_for_prompt(tree)}
        
        Check for:
        1. Contradictory paths (same condition leading to different outcomes)
        2. Circular dependencies
        3. Unreachable nodes
        4. Missing decision paths
        5. Incorrect boolean logic
        
        Return any issues found with specific node IDs and explanations.
        """
        
        validation_result = self.llm.generate_structured_json(
            prompt=prompt,
            response_schema=LogicalConsistencyCheck
        )
        return validation_result.model_dump()

    def _check_completeness(self, tree: dict) -> dict:
        # Placeholder for completeness check
        return {}

    def _check_ambiguity(self, tree: dict) -> dict:
        # Placeholder for ambiguity check
        return {}

    def _parse_validation_response(self, response: str) -> dict:
        # This method is no longer needed as generate_structured_json returns a Pydantic object
        return {}

    def _test_edge_cases(self, tree: dict) -> dict:
        test_scenarios = [
            {
                "description": "Elderly patient with multiple comorbidities",
                "inputs": {"age": 85, "egfr": 25, "has_diabetes": True}
            },
            {
                "description": "Young adult newly diagnosed",
                "inputs": {"age": 19, "hba1c": 14.0, "prior_therapy": False}
            },
            # ... more test cases
        ]
        
        results = []
        for scenario in test_scenarios:
            path = self._traverse_tree(tree, scenario["inputs"])
            results.append({
                "scenario": scenario["description"],
                "path": path,
                "outcome": path[-1]["decision"] if path else "No outcome reached"
            })
        
        return {"suggestions": self._analyze_test_results(results)}

    def _traverse_tree(self, tree: dict, inputs: dict) -> list:
        # Placeholder for tree traversal logic
        return []

    def _analyze_test_results(self, results: list) -> list:
        # Placeholder for analyzing test results
        return []
    
    def _detect_contradictory_paths(self, tree: dict) -> List[Dict]:
        """Detect paths that lead to different outcomes for the same conditions."""
        conflicts = []
        nodes = tree.get('nodes', {})
        
        # Build a map of conditions to their outcomes
        condition_outcomes = {}
        
        # Convert nodes dict to list if it's a dictionary
        if isinstance(nodes, dict):
            nodes_list = list(nodes.values())
        else:
            nodes_list = nodes
        
        for node in nodes_list:
            if node.get('type') == 'decision':
                condition = node.get('condition', '')
                outcomes = set()
                
                # Find all possible outcomes from this node
                for connection in node.get('connections', []):
                    target_node = self._find_node_by_id(nodes, connection.get('to'))
                    if target_node and target_node.get('type') == 'outcome':
                        outcomes.add(target_node.get('decision', ''))
                
                if condition in condition_outcomes:
                    if condition_outcomes[condition] != outcomes:
                        conflicts.append({
                            'type': ConflictType.CONTRADICTORY_PATHS.value,
                            'description': f'Condition "{condition}" leads to different outcomes',
                            'nodes': [node['id']],
                            'severity': 'high'
                        })
                else:
                    condition_outcomes[condition] = outcomes
        
        return conflicts
    
    def _detect_circular_dependencies(self, tree: dict) -> List[Dict]:
        """Detect circular references in the tree structure."""
        conflicts = []
        
        try:
            # Use the existing circular reference detection utility
            circular_refs = detect_circular_references(tree)
            
            for cycle in circular_refs:
                conflicts.append({
                    'type': ConflictType.CIRCULAR_DEPENDENCY.value,
                    'description': f'Circular dependency detected: {" -> ".join(cycle)}',
                    'nodes': cycle,
                    'severity': 'critical'
                })
        except Exception as e:
            if self.verbose:
                print(f"   Error detecting circular dependencies: {e}")
        
        return conflicts
    
    def _detect_redundant_paths(self, tree: dict) -> List[Dict]:
        """Detect paths that reach the same outcome with identical conditions."""
        conflicts = []
        nodes = tree.get('nodes', {})
        
        # Map outcomes to their paths
        outcome_paths = {}
        
        # Convert nodes dict to list if it's a dictionary
        if isinstance(nodes, dict):
            nodes_list = list(nodes.values())
        else:
            nodes_list = nodes
        
        try:
            # Find all outcome nodes first
            outcome_nodes = [n for n in nodes_list if n.get('decision') is not None]
            
            # For each outcome, find all paths from possible start nodes
            for outcome_node in outcome_nodes:
                # Find potential starting nodes
                # First, find nodes that are not targets of any connections
                referenced_nodes = set()
                for node in nodes_list:
                    connections = node.get('connections', {})
                    if isinstance(connections, dict):
                        referenced_nodes.update(connections.values())
                    elif isinstance(connections, list):
                        for conn in connections:
                            if isinstance(conn, dict) and 'to' in conn:
                                referenced_nodes.add(conn['to'])
                
                # Starting nodes are those not referenced by others
                start_nodes = [n for n in nodes_list if n.get('id') not in referenced_nodes]
                
                # If no clear start nodes, use nodes that are not outcome nodes
                if not start_nodes:
                    start_nodes = [n for n in nodes_list if n.get('decision') is None]
                
                for start_node in start_nodes:
                    paths = find_all_paths(tree, start_node.get('id'), outcome_node.get('id'))
                    
                    for path in paths:
                        if path:
                            outcome = outcome_node.get('decision', '')
                            conditions = []
                            path_node_ids = []
                            
                            # Extract conditions along the path
                            # Handle both node ID strings and node objects (for mocked tests)
                            for item in path[:-1]:
                                if isinstance(item, dict):
                                    # Mock returns node objects
                                    node = item
                                    node_id = node.get('id')
                                    condition_text = node.get('question') or node.get('condition')
                                else:
                                    # Real implementation returns node IDs
                                    node_id = item
                                    node = self._find_node_by_id(nodes, node_id)
                                    condition_text = node.get('question') or node.get('condition') if node else None
                                
                                if node_id:
                                    path_node_ids.append(node_id)
                                if condition_text:
                                    conditions.append(condition_text)
                            
                            # Add the last node ID
                            last_item = path[-1] if path else None
                            if last_item:
                                if isinstance(last_item, dict):
                                    path_node_ids.append(last_item.get('id'))
                                else:
                                    path_node_ids.append(last_item)
                            
                            condition_str = ' -> '.join(conditions)
                            
                            if outcome not in outcome_paths:
                                outcome_paths[outcome] = []
                            outcome_paths[outcome].append({
                                'conditions': condition_str,
                                'nodes': path_node_ids
                            })
        except Exception as e:
            if self.verbose:
                print(f"   Error detecting redundant paths: {e}")
        
        # Check for redundant paths
        for outcome, paths in outcome_paths.items():
            condition_sets = {}
            for path in paths:
                cond = path['conditions']
                # Only consider it redundant if there are actual conditions (not empty paths)
                if cond and cond in condition_sets:
                    conflicts.append({
                        'type': ConflictType.REDUNDANT_PATHS.value,
                        'description': f'Multiple paths with identical conditions lead to "{outcome}"',
                        'nodes': path['nodes'] + condition_sets[cond],
                        'severity': 'medium'
                    })
                elif cond:  # Only track non-empty condition strings
                    condition_sets[cond] = path['nodes']
        
        return conflicts
    
    def _detect_overlapping_conditions(self, tree: dict) -> List[Dict]:
        """Detect conditions that overlap or are mutually exclusive."""
        conflicts = []
        nodes = tree.get('nodes', {})
        
        # Convert nodes dict to list if it's a dictionary
        if isinstance(nodes, dict):
            nodes_list = list(nodes.values())
        else:
            nodes_list = nodes
        
        decision_nodes = [n for n in nodes_list if n.get('type') == 'decision']
        
        # Compare pairs of decision nodes
        for i, node1 in enumerate(decision_nodes):
            for node2 in decision_nodes[i+1:]:
                condition1 = node1.get('condition', '')
                condition2 = node2.get('condition', '')
                
                # Simple overlap detection based on condition similarity
                if self._conditions_overlap(condition1, condition2):
                    conflicts.append({
                        'type': ConflictType.OVERLAPPING_CONDITIONS.value,
                        'description': f'Conditions may overlap: "{condition1}" and "{condition2}"',
                        'nodes': [node1['id'], node2['id']],
                        'severity': 'low'
                    })
        
        return conflicts
    
    def _find_node_by_id(self, nodes, node_id: str) -> dict:
        """Find a node by its ID."""
        # Handle both dict and list formats
        if isinstance(nodes, dict):
            return nodes.get(node_id)
        else:
            for node in nodes:
                if node.get('id') == node_id:
                    return node
        return None
    
    def _conditions_overlap(self, condition1: str, condition2: str) -> bool:
        """Simple check for overlapping conditions."""
        # This is a simplified implementation
        # In practice, you'd want more sophisticated logic
        
        # Check for common keywords that might indicate overlap
        keywords1 = set(condition1.lower().split())
        keywords2 = set(condition2.lower().split())
        
        # If conditions share significant keywords, they might overlap
        common_keywords = keywords1.intersection(keywords2)
        
        # Exclude common words
        common_words = {'is', 'the', 'and', 'or', 'not', 'has', 'have', 'with', 'than', 'greater', 'less'}
        significant_common = common_keywords - common_words
        
        return len(significant_common) >= 2
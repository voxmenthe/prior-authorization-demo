from typing import List, Dict, Set, Tuple, Any, Optional
from src.core.llm_client import LlmClient
from src.core.schemas import LogicalConsistencyCheck, CompletenessCheck, AmbiguityCheck
from src.core.exceptions import ConflictType
from src.utils.tree_traversal import find_all_paths, detect_circular_references
from src.utils.json_utils import sanitize_json_for_prompt
from src.core.config import get_config

class ValidationAgent:
    def __init__(self, verbose: bool = False, max_retries: int = None):
        self.verbose = verbose
        self.config = get_config()
        # Use provided max_retries or fall back to config
        self.max_retries = max_retries if max_retries is not None else self.config.validation_max_retries
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
        
        # Check for logical consistency with improved error handling
        logic_check = self._check_logical_consistency_with_retry(tree)
        
        # Validate and clean the issues before adding them
        validated_issues = self._validate_issues_format(logic_check.get("issues", []))
        validation_results["issues"].extend(validated_issues)
        
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
        """Check if all medical criteria are covered by the tree."""
        if self.verbose:
            print("   Checking tree completeness...")
            
        # Get the original parsed criteria from the tree metadata if available
        original_criteria = tree.get('metadata', {}).get('original_criteria', [])
        
        prompt = f"""
        Analyze if this decision tree covers all medical criteria comprehensively:
        
        Tree: {sanitize_json_for_prompt(tree)}
        
        Original Criteria Count: {len(original_criteria) if original_criteria else 'Unknown'}
        
        Check for:
        1. Missing medical criteria not addressed in any decision path
        2. Incomplete decision pathways that end prematurely without reaching an outcome
        3. Criteria mentioned in questions but not fully evaluated
        4. Edge cases or exceptions that should be covered but aren't
        5. Missing validation rules or thresholds for clinical values
        
        For each issue found, specify:
        - Issue type: 'missing_criteria', 'incomplete_pathway', or 'unaddressed_edge_case'
        - Detailed description of what's missing
        - Which specific criteria are not covered (if applicable)
        - Which nodes are affected or where new nodes should be added
        
        Focus on medical completeness - ensure all clinical scenarios lead to a clear decision.
        """
        
        try:
            completeness_result = self.llm.generate_structured_json(
                prompt=prompt,
                response_schema=CompletenessCheck
            )
            
            # Convert CompletenessIssue objects to ValidationIssue format
            issues = []
            for issue in completeness_result.issues:
                validation_issue = issue.to_validation_issue()
                issues.append({
                    'node_id': validation_issue.node_id,
                    'explanation': validation_issue.explanation
                })
                
            return {"issues": issues}
            
        except Exception as e:
            if self.verbose:
                print(f"   ⚠️  Error in completeness check: {e}")
            return {"issues": []}

    def _check_ambiguity(self, tree: dict) -> dict:
        """Check for vague or unclear conditions in the tree."""
        if self.verbose:
            print("   Checking for ambiguous conditions...")
            
        prompt = f"""
        Analyze this decision tree for ambiguous or unclear language:
        
        Tree: {sanitize_json_for_prompt(tree)}
        
        Check each node for:
        1. Vague conditions without specific thresholds (e.g., "high blood pressure" without mmHg values)
        2. Unclear terminology that could be interpreted multiple ways
        3. Missing units of measurement for clinical values
        4. Subjective terms that need objective criteria (e.g., "severe", "mild", "frequent")
        5. Incomplete boolean logic or missing operators
        6. Time-based criteria without specific durations
        
        For each ambiguous node found, provide:
        - The node ID
        - The specific ambiguous text
        - Type of ambiguity: 'vague_condition', 'missing_threshold', 'unclear_terminology', 'subjective_term', 'missing_units', or 'incomplete_logic'
        - A concrete suggestion for how to make it clearer
        
        Focus on medical precision - all conditions should be objectively evaluable.
        """
        
        try:
            ambiguity_result = self.llm.generate_structured_json(
                prompt=prompt,
                response_schema=AmbiguityCheck
            )
            
            # Convert AmbiguityIssue objects to ValidationIssue format
            issues = []
            for issue in ambiguity_result.issues:
                validation_issue = issue.to_validation_issue()
                issues.append({
                    'node_id': validation_issue.node_id,
                    'explanation': validation_issue.explanation
                })
                
            return {"issues": issues}
            
        except Exception as e:
            if self.verbose:
                print(f"   ⚠️  Error in ambiguity check: {e}")
            return {"issues": []}

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
            
            # Determine the outcome from the path
            outcome = "No outcome reached"
            if path:
                last_node = path[-1]
                if last_node.get("type") == "outcome":
                    outcome = last_node.get("decision", "Unknown outcome")
                else:
                    # If last node is not an outcome, path may be incomplete
                    outcome = f"Incomplete path - ended at {last_node.get('type', 'unknown')} node"
            
            results.append({
                "scenario": scenario["description"],
                "path": path,
                "outcome": outcome
            })
        
        return {"suggestions": self._analyze_test_results(results)}

    def _traverse_tree(self, tree: dict, inputs: dict) -> list:
        """Traverse the tree with given inputs to find the path taken."""
        if self.verbose:
            print(f"   Traversing tree with inputs: {inputs}")
            
        path = []
        nodes = tree.get('nodes', {})
        
        # Find the start node
        start_node_id = tree.get('metadata', {}).get('start_node_id')
        if not start_node_id:
            # Try to find a node that's not referenced by any other node
            referenced_nodes = set()
            for node in nodes.values() if isinstance(nodes, dict) else nodes:
                connections = node.get('connections', {})
                if isinstance(connections, dict):
                    referenced_nodes.update(connections.values())
                elif isinstance(connections, list):
                    for conn in connections:
                        if isinstance(conn, dict) and 'to' in conn:
                            referenced_nodes.add(conn['to'])
                            
            # Find nodes not referenced by others
            all_node_ids = set(nodes.keys() if isinstance(nodes, dict) else [n.get('id') for n in nodes])
            potential_starts = all_node_ids - referenced_nodes
            
            if potential_starts:
                start_node_id = list(potential_starts)[0]
            else:
                # Fallback: use first node
                if isinstance(nodes, dict) and nodes:
                    start_node_id = list(nodes.keys())[0]
                elif isinstance(nodes, list) and nodes:
                    start_node_id = nodes[0].get('id')
                    
        if not start_node_id:
            if self.verbose:
                print("   ⚠️  Could not find start node")
            return []
            
        # Traverse from start node
        current_node_id = start_node_id
        visited = set()
        
        while current_node_id:
            if current_node_id in visited:
                # Circular reference detected
                if self.verbose:
                    print(f"   ⚠️  Circular reference detected at node {current_node_id}")
                break
                
            visited.add(current_node_id)
            
            # Get current node
            current_node = self._find_node_by_id(nodes, current_node_id)
            if not current_node:
                if self.verbose:
                    print(f"   ⚠️  Node {current_node_id} not found")
                break
                
            path.append(current_node)
            
            # Check if this is an outcome node
            if current_node.get('type') == 'outcome' or current_node.get('decision') is not None:
                # Reached an outcome
                break
                
            # Evaluate connections to find next node
            next_node_id = self._evaluate_node_connections(current_node, inputs, nodes)
            
            if not next_node_id:
                # No valid connection found
                if self.verbose:
                    print(f"   No valid connection from node {current_node_id}")
                break
                
            current_node_id = next_node_id
            
        return path

    def _analyze_test_results(self, results: list) -> list:
        """Analyze edge case test results and provide suggestions."""
        suggestions = []
        
        # Check for scenarios that didn't reach an outcome
        no_outcome_scenarios = [r for r in results if r['outcome'] == "No outcome reached"]
        if no_outcome_scenarios:
            scenarios_list = ", ".join([r['scenario'] for r in no_outcome_scenarios])
            suggestions.append(f"The following scenarios did not reach a clear outcome: {scenarios_list}. Consider adding decision paths for these cases.")
            
        # Check for scenarios that all lead to the same outcome (potential missing differentiation)
        outcomes = [r['outcome'] for r in results if r['outcome'] != "No outcome reached"]
        if len(set(outcomes)) == 1 and len(outcomes) > 2:
            suggestions.append(f"All test scenarios lead to the same outcome: '{outcomes[0]}'. Consider if more nuanced decision criteria are needed.")
            
        # Check for very short paths (might indicate incomplete evaluation)
        short_paths = [r for r in results if len(r.get('path', [])) < 3 and r['outcome'] != "No outcome reached"]
        if short_paths:
            suggestions.append(f"{len(short_paths)} scenarios reached outcomes with very few decision points. Consider if additional criteria should be evaluated.")
            
        return suggestions
    
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
                connections = node.get('connections', {})
                
                # Handle both dict and list formats
                if isinstance(connections, dict):
                    # Dict format: {"yes": "node_id", "no": "other_node_id"}
                    for condition_key, target_id in connections.items():
                        target_node = self._find_node_by_id(nodes, target_id)
                        if target_node and target_node.get('type') == 'outcome':
                            outcomes.add(target_node.get('decision', ''))
                elif isinstance(connections, list):
                    # List format: [{"to": "node_id", ...}, ...]
                    for connection in connections:
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
    
    # Enhanced methods for handling malformed LLM responses
    def _check_logical_consistency_with_retry(self, tree: dict) -> dict:
        """Check logical consistency with retry logic for malformed responses."""
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                if attempt > 0 and self.verbose:
                    print(f"   Retry {attempt}/{self.max_retries} for logical consistency check...")
                
                result = self._check_logical_consistency_v2(tree, attempt, last_error)
                
                # Validate the result
                if self._is_valid_consistency_result(result):
                    return result
                else:
                    last_error = "Response format validation failed"
                    if attempt == self.max_retries:
                        # On last attempt, try to salvage what we can
                        return self._salvage_consistency_result(result)
                        
            except Exception as e:
                last_error = str(e)
                if attempt == self.max_retries:
                    # Return empty result on final failure
                    if self.verbose:
                        print(f"   ⚠️  All retries failed for consistency check: {e}")
                    return {"issues": []}
        
        return {"issues": []}
    
    def _check_logical_consistency_v2(self, tree: dict, attempt: int = 0, last_error: str = None) -> dict:
        """Enhanced version of logical consistency check with better prompts."""
        # Build prompt with progressive enhancements based on attempt
        base_prompt = f"""
        Analyze this decision tree for logical inconsistencies:
        
        Tree: {sanitize_json_for_prompt(tree)}
        
        Check for:
        1. Contradictory paths (same condition leading to different outcomes)
        2. Circular dependencies (nodes that form loops)
        3. Unreachable nodes (nodes with no incoming connections except start_node)
        4. Missing decision paths (decision nodes with no outgoing connections)
        5. Incorrect boolean logic
        """
        
        if attempt == 0:
            # First attempt: clear but not overly prescriptive
            prompt = base_prompt + """
        
        Return a JSON object with an 'issues' array containing any problems found.
        Each issue must be an object with 'node_id' and 'explanation' fields.
        
        Example format:
        {
          "issues": [
            {"node_id": "n1", "explanation": "This node has no outgoing connections"},
            {"node_id": "n2", "explanation": "Circular dependency: n2 -> n3 -> n2"}
          ]
        }
        """
        else:
            # Retry attempt: more explicit instructions
            prompt = base_prompt + f"""
        
        IMPORTANT: Your previous response had an error: {last_error}
        
        You MUST return ONLY a valid JSON object with this EXACT structure:
        {{
          "issues": [
            {{"node_id": "<string>", "explanation": "<string>"}},
            {{"node_id": "<string>", "explanation": "<string>"}}
          ]
        }}
        
        Rules:
        - The response must be valid JSON (no code blocks, no markdown, no extra text)
        - The "issues" field must be an array (use [] for empty)
        - Each item in the array must be an object with exactly two fields: "node_id" and "explanation"
        - Both fields must be strings
        - Do not include any other fields or text
        
        If there are no issues, return: {{"issues": []}}
        """
        
        # If it's a retry, fall back to original method to maintain compatibility
        if attempt == 0:
            return self._check_logical_consistency(tree)
        else:
            # Use enhanced prompt for retries
            validation_result = self.llm.generate_structured_json(
                prompt=prompt,
                response_schema=LogicalConsistencyCheck
            )
            return validation_result.model_dump()
    
    def _is_valid_consistency_result(self, result: Any) -> bool:
        """Validate that the consistency check result has the expected format."""
        if not isinstance(result, dict):
            return False
            
        if 'issues' not in result:
            return False
            
        issues = result.get('issues', [])
        if not isinstance(issues, list):
            return False
            
        # Check each issue
        for issue in issues:
            if not isinstance(issue, dict):
                return False
            if 'node_id' not in issue or 'explanation' not in issue:
                return False
            if not isinstance(issue['node_id'], str) or not isinstance(issue['explanation'], str):
                return False
                
        return True
    
    def _salvage_consistency_result(self, result: Any) -> dict:
        """Try to salvage a malformed consistency result."""
        if self.verbose:
            print("   🔧 Attempting to salvage malformed consistency result...")
            
        salvaged = {"issues": []}
        
        if isinstance(result, dict) and 'issues' in result:
            issues = result['issues']
            if isinstance(issues, list):
                for item in issues:
                    if isinstance(item, dict) and 'node_id' in item and 'explanation' in item:
                        # Valid issue, keep it
                        salvaged['issues'].append(item)
                    elif isinstance(item, str):
                        # String issue - try to parse it
                        parsed = self._parse_string_issue(item)
                        if parsed:
                            salvaged['issues'].append(parsed)
                            
        return salvaged
    
    def _parse_string_issue(self, issue_str: str) -> dict:
        """Try to parse a string issue into proper format."""
        # Common patterns in malformed issues
        patterns = [
            # "circular_dependency: n1 -> n2 -> n1"
            (r'circular_dependency:\s*(.+)', 'circular'),
            # "redundant_paths: ..."
            (r'redundant_paths:\s*(.+)', 'redundant'),
            # "Node n1: ..."
            (r'Node\s+(\w+):\s*(.+)', 'node_specific'),
        ]
        
        import re
        for pattern, issue_type in patterns:
            match = re.match(pattern, issue_str, re.IGNORECASE)
            if match:
                if issue_type == 'circular':
                    # Extract nodes from path
                    path = match.group(1)
                    nodes = re.findall(r'n\d+', path)
                    if nodes:
                        return {
                            'node_id': nodes[0],
                            'explanation': f'Circular dependency detected: {path}'
                        }
                elif issue_type == 'redundant':
                    # Try to extract node references from the whole string
                    nodes = re.findall(r'n\d+|node\s+\w+|outcome\d+', issue_str, re.IGNORECASE)
                    if nodes:
                        # Clean up node references
                        node_id = nodes[0].replace('node ', '').strip()
                        return {
                            'node_id': node_id,
                            'explanation': f'Redundant paths: {match.group(1)}'
                        }
                    else:
                        # No specific nodes mentioned, use generic
                        return {
                            'node_id': 'unknown',
                            'explanation': issue_str
                        }
                elif issue_type == 'node_specific':
                    return {
                        'node_id': match.group(1),
                        'explanation': match.group(2)
                    }
                    
        # Fallback: create generic issue
        nodes = re.findall(r'n\d+', issue_str)
        if nodes:
            return {
                'node_id': nodes[0],
                'explanation': issue_str
            }
            
        return None
    
    def _validate_issues_format(self, issues: List[Any]) -> List[Dict]:
        """Ensure all issues are in the correct format."""
        validated = []
        
        for issue in issues:
            if isinstance(issue, dict) and 'node_id' in issue and 'explanation' in issue:
                # Already valid
                validated.append(issue)
            elif isinstance(issue, str):
                # Try to parse string issue
                if self.verbose:
                    print(f"   ⚠️  Found string issue: {issue[:50]}...")
                parsed = self._parse_string_issue(issue)
                if parsed:
                    validated.append(parsed)
            elif hasattr(issue, 'node_id') and hasattr(issue, 'explanation'):
                # Pydantic model - convert to dict
                validated.append({
                    'node_id': issue.node_id,
                    'explanation': issue.explanation
                })
                
        return validated
    
    def _evaluate_node_connections(self, node: dict, inputs: dict, nodes: dict) -> Optional[str]:
        """Evaluate node connections against inputs to determine next node."""
        connections = node.get('connections', {})
        
        # Handle different connection formats
        if isinstance(connections, dict):
            # Old format: direct mapping of conditions to node IDs
            for condition, target_node_id in connections.items():
                if self._evaluate_condition(condition, inputs, node):
                    return target_node_id
        elif isinstance(connections, list):
            # New format: list of connection objects
            for conn in connections:
                if isinstance(conn, dict):
                    condition = conn.get('condition', '')
                    target_node_id = conn.get('to') or conn.get('target_node_id')
                    if self._evaluate_condition(condition, inputs, node):
                        return target_node_id
                        
        return None
    
    def _evaluate_condition(self, condition: str, inputs: dict, node: dict) -> bool:
        """Evaluate if a condition is met given the inputs."""
        # Simple evaluation logic - can be enhanced
        condition_lower = condition.lower()
        
        # Handle boolean conditions
        if condition_lower in ['yes', 'true', 'approved']:
            return True
        elif condition_lower in ['no', 'false', 'denied']:
            return False
            
        # Handle numeric comparisons
        # Look for patterns like "age > 18" or "egfr < 30"
        import re
        numeric_pattern = r'(\w+)\s*([><=]+)\s*([\d.]+)'
        match = re.search(numeric_pattern, condition)
        
        if match:
            param_name = match.group(1).lower()
            operator = match.group(2)
            threshold = float(match.group(3))
            
            # Find matching input
            input_value = None
            for key, value in inputs.items():
                if key.lower() == param_name or param_name in key.lower():
                    try:
                        input_value = float(value)
                        break
                    except (ValueError, TypeError):
                        continue
                        
            if input_value is not None:
                if operator == '>':
                    return input_value > threshold
                elif operator == '>=':
                    return input_value >= threshold
                elif operator == '<':
                    return input_value < threshold
                elif operator == '<=':
                    return input_value <= threshold
                elif operator == '==' or operator == '=':
                    return input_value == threshold
                    
        # Default: assume condition is met if we can't evaluate it
        return True
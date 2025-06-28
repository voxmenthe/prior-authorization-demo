import json
from src.core.llm_client import LlmClient
from src.core.schemas import QuestionOrder, DecisionNode
from src.core.exceptions import TreeStructureError
from src.utils.json_utils import sanitize_json_for_prompt

class TreeStructureAgent:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.llm = LlmClient(verbose=verbose)
        if verbose:
            print("🌳 TreeStructureAgent initialized")
        
    def create_tree(self, parsed_criteria: dict) -> dict:
        if self.verbose:
            print(f"\n🔧 Building decision tree structure")
        
        # Generate optimal question ordering
        if self.verbose:
            print("   Determining optimal question order...")
        question_sequence = self._determine_question_order(parsed_criteria)
        
        if self.verbose:
            print(f"   ✅ Question sequence: {len(question_sequence)} criteria")
        
        # Build tree nodes
        nodes = []
        node_id_counter = 1
        
        if self.verbose:
            print("   Creating decision nodes...")
        
        for i, criterion in enumerate(question_sequence):
            if self.verbose:
                criterion_id = criterion.get('id', 'unknown') if isinstance(criterion, dict) else str(criterion)
                print(f"   Creating node {i+1}/{len(question_sequence)}: {criterion_id}")
            
            node = self._create_node_from_criterion(
                criterion, 
                node_id=f"n{node_id_counter}",
                is_last=(i == len(question_sequence) - 1)
            )
            nodes.append(node)
            node_id_counter += 1
        
        # Add outcome nodes
        if self.verbose:
            print("   Adding outcome nodes...")
        outcome_nodes = self._generate_outcome_nodes(parsed_criteria)
        nodes.extend(outcome_nodes)
        
        # Connect nodes
        if self.verbose:
            print("   Connecting nodes...")
        connected_tree = self._connect_nodes(nodes, parsed_criteria)
        
        if self.verbose:
            print(f"   ✅ Tree structure complete: {len(nodes)} total nodes")
        
        return connected_tree
    
    def _determine_question_order(self, criteria: dict) -> list:
        prompt = f"""
        Given these clinical criteria, determine the optimal order for asking questions in a decision tree 
        that leads to efficient APPROVE/DENY decisions.

        Consider:
        1. Most exclusionary criteria first (likely to result in DENIAL - fail fast)
        2. Expensive/complex checks last (only if cheaper checks pass)
        3. Logical medical workflow (diagnosis -> eligibility -> contraindications -> documentation)
        4. Group related criteria to minimize cognitive load
        5. Put documentation requirements at the end (assuming clinical criteria pass)

        Criteria: {sanitize_json_for_prompt(criteria)}

        IMPORTANT: Order criteria to minimize total questions needed for most common denial reasons.
        Exclusionary criteria should be checked before inclusionary criteria when possible.

        Return an ordered list of criterion IDs with reasoning for the order that optimizes for 
        both user experience and processing efficiency.
        """
        
        try:
            question_order = self.llm.generate_structured_json(
                prompt=prompt,
                response_schema=QuestionOrder
            )
            return question_order.ordered_ids
        except Exception as e:
            raise TreeStructureError(f"Failed to determine question order: {str(e)}") from e

    def _parse_ordering_response(self, response: str) -> list:
        # This method is no longer needed as generate_structured_json returns a Pydantic object
        # and we directly access ordered_ids.
        return []
    
    def _create_node_from_criterion(self, criterion: dict, node_id: str, is_last: bool) -> dict:
        prompt = f"""
        Convert this clinical criterion into a decision tree node question.
        
        Criterion: {sanitize_json_for_prompt(criterion)}
        
        Guidelines:
        1. Make the question clear and unambiguous
        2. Use medical terminology appropriately but include help text
        3. Specify the expected answer format (yes/no, multiple choice, numeric)
        4. Include validation rules for data entry
        
        Return a JSON node structure with id '{node_id}'.
        """
        
        try:
            node = self.llm.generate_structured_json(
                prompt=prompt,
                response_schema=DecisionNode
            )
            return node.model_dump()
        except Exception as e:
            raise TreeStructureError(f"Failed to create node from criterion: {str(e)}") from e

    def _generate_outcome_nodes(self, parsed_criteria: dict) -> list:
        # Use enhanced criteria parser if available
        try:
            from src.core.criteria_parser import CriteriaParser
            parser = CriteriaParser()
            enhanced_criteria = parser.enhance_criteria_relationships(parsed_criteria)
        except ImportError:
            enhanced_criteria = parsed_criteria
        
        # Generate specific denial outcomes for each criterion type
        outcome_nodes = []
        
        # APPROVED outcome
        outcome_nodes.append({
            "id": "approved",
            "type": "outcome",
            "decision": "APPROVED",
            "message": "Prior authorization approved. All required criteria have been met.",
            "criteria_reference": "All criteria sections satisfied",
            "next_steps": "Proceed with prescribed treatment. Monitor patient response and adhere to any ongoing requirements.",
            "metadata": {
                "approval_type": "full",
                "requires_monitoring": True
            }
        })
        
        # Generate specific DENIED outcomes based on criteria types
        criteria_list = parsed_criteria.get("criteria_list", [])
        
        # Denied for exclusionary criteria
        exclusionary_criteria = [c for c in criteria_list if c.get("type") == "EXCLUSIONARY"]
        for criterion in exclusionary_criteria:
            outcome_nodes.append({
                "id": f"denied_{criterion['id']}",
                "type": "outcome",
                "decision": "DENIED",
                "message": f"Prior authorization denied due to exclusionary condition: {criterion.get('description', criterion['id'])}",
                "criteria_reference": criterion["id"],
                "next_steps": "This is an absolute contraindication. Alternative treatment options should be considered.",
                "metadata": {
                    "denial_type": "exclusionary",
                    "criterion_violated": criterion["id"],
                    "is_appealable": False
                }
            })
        
        # Denied for missing required criteria
        required_criteria = [c for c in criteria_list if c.get("type") in ["REQUIRED", "THRESHOLD"]]
        for criterion in required_criteria:
            outcome_nodes.append({
                "id": f"denied_{criterion['id']}_missing",
                "type": "outcome", 
                "decision": "DENIED",
                "message": f"Prior authorization denied: Required criterion not met - {criterion.get('description', criterion['id'])}",
                "criteria_reference": criterion["id"],
                "next_steps": "Obtain required documentation or meet the specified criteria, then resubmit request.",
                "metadata": {
                    "denial_type": "missing_requirement",
                    "criterion_violated": criterion["id"],
                    "is_appealable": True
                }
            })
        
        # Denied for missing documentation
        documentation_criteria = [c for c in criteria_list if c.get("type") == "DOCUMENTATION"]
        for criterion in documentation_criteria:
            outcome_nodes.append({
                "id": f"denied_{criterion['id']}_docs",
                "type": "outcome",
                "decision": "DENIED", 
                "message": f"Prior authorization denied: Missing required documentation - {criterion.get('description', criterion['id'])}",
                "criteria_reference": criterion["id"],
                "next_steps": "Submit the required documentation and resubmit the prior authorization request.",
                "metadata": {
                    "denial_type": "missing_documentation",
                    "criterion_violated": criterion["id"],
                    "is_appealable": True
                }
            })
        
        # General denial fallback
        outcome_nodes.append({
            "id": "denied_general",
            "type": "outcome",
            "decision": "DENIED",
            "message": "Prior authorization denied. One or more criteria not satisfied.",
            "criteria_reference": "Multiple criteria",
            "next_steps": "Review all criteria requirements and provide missing information. Contact provider for guidance.",
            "metadata": {
                "denial_type": "general",
                "is_appealable": True
            }
        })
        
        if self.verbose:
            print(f"   ✅ Generated {len(outcome_nodes)} specific outcome nodes")
            
        return outcome_nodes

    def _connect_nodes(self, nodes: list, parsed_criteria: dict) -> dict:
        prompt = f"""
        Connect these decision tree nodes with proper logic flow to reach APPROVE/DENY decisions:
        
        Nodes: {sanitize_json_for_prompt(nodes)}
        Criteria: {sanitize_json_for_prompt(parsed_criteria)}
        
        Connection Logic Rules:
        1. Start with most exclusionary criteria first (fail-fast approach)
        2. Each question node should connect to:
           - Next question on success (if not final)
           - Appropriate DENIED outcome on failure
           - APPROVED outcome only after all criteria pass
        3. Ensure every path leads to a definitive decision
        4. No orphaned nodes - every node must be reachable
        
        Return the complete tree structure with all connections properly mapped.
        Format as:
        {{
            "start_node": "id_of_first_node",
            "nodes": {{
                "node_id": {{
                    "...node_data...",
                    "connections": {{
                        "yes": "next_node_id_on_success",
                        "no": "denied_outcome_id_on_failure"
                    }}
                }}
            }}
        }}
        """
        
        try:
            response = self.llm.generate_text(prompt)
            # Parse the JSON response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                connected_tree = json.loads(json_match.group())
                # Fix connections that might have dict values instead of string node IDs
                connected_tree = self._fix_connections_format(connected_tree)
                if self.verbose:
                    print(f"   ✅ Connected {len(connected_tree.get('nodes', {}))} nodes")
                return connected_tree
            else:
                # Fallback: create basic linear connection
                return self._create_fallback_connections(nodes)
        except Exception as e:
            if self.verbose:
                print(f"   ⚠️ Error connecting nodes: {str(e)}")
            return self._create_fallback_connections(nodes)
    
    def _fix_connections_format(self, tree: dict) -> dict:
        """
        Fix connections that have dict values instead of string node IDs.
        
        Sometimes the LLM returns full node objects in connections instead of just IDs.
        This method ensures connections only contain string node IDs.
        """
        nodes = tree.get('nodes', {})
        
        for node_id, node in nodes.items():
            connections = node.get('connections', {})
            
            if isinstance(connections, dict):
                # Fix dict-style connections (e.g., {"yes": ..., "no": ...})
                fixed_connections = {}
                for condition, target in connections.items():
                    if isinstance(target, dict):
                        # Extract the ID from the dict
                        target_id = target.get('id')
                        if target_id:
                            fixed_connections[condition] = target_id
                        else:
                            if self.verbose:
                                print(f"   ⚠️ Warning: No ID found in connection dict for {node_id}[{condition}]")
                    else:
                        # Already a string or other valid format
                        fixed_connections[condition] = target
                
                node['connections'] = fixed_connections
                
            elif isinstance(connections, list):
                # Fix list-style connections (e.g., [{"target_node_id": ..., "condition": ...}])
                fixed_connections = []
                for conn in connections:
                    if isinstance(conn, dict):
                        # Check if target_node_id is a dict instead of string
                        target = conn.get('target_node_id')
                        if isinstance(target, dict):
                            # Extract the ID from the dict
                            target_id = target.get('id')
                            if target_id:
                                conn['target_node_id'] = target_id
                            else:
                                if self.verbose:
                                    print(f"   ⚠️ Warning: No ID found in connection target dict for {node_id}")
                        fixed_connections.append(conn)
                    else:
                        # Keep as is if not a dict
                        fixed_connections.append(conn)
                
                node['connections'] = fixed_connections
        
        return tree
    
    def _create_fallback_connections(self, nodes: list) -> dict:
        """Create a basic linear connection between nodes as fallback"""
        if not nodes:
            return {"nodes": {}}
        
        # Separate question nodes from outcome nodes
        question_nodes = [n for n in nodes if n.get("type") != "outcome"]
        outcome_nodes = [n for n in nodes if n.get("type") == "outcome"]
        
        # Find APPROVED and DENIED outcomes
        approved_node = next((n for n in outcome_nodes if n.get("decision") == "APPROVED"), None)
        denied_node = next((n for n in outcome_nodes if n.get("decision") == "DENIED"), None)
        
        # Build connections
        tree_nodes = {}
        start_node = None
        
        # Add all nodes to tree
        for node in nodes:
            tree_nodes[node["id"]] = node.copy()
        
        # Connect question nodes in sequence
        for i, node in enumerate(question_nodes):
            node_id = node["id"]
            if i == 0:
                start_node = node_id
            
            # Add connections
            if i < len(question_nodes) - 1:
                # Not the last question - connect to next question on success
                next_node_id = question_nodes[i + 1]["id"]
                tree_nodes[node_id]["connections"] = {
                    "yes": next_node_id,
                    "no": denied_node["id"] if denied_node else "denied_general"
                }
            else:
                # Last question - connect to final outcomes
                tree_nodes[node_id]["connections"] = {
                    "yes": approved_node["id"] if approved_node else "approved",
                    "no": denied_node["id"] if denied_node else "denied_general"
                }
        
        return {
            "start_node": start_node or (nodes[0]["id"] if nodes else None),
            "nodes": tree_nodes
        }
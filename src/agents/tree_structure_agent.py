import json
from src.core.llm_client import LlmClient
from src.core.schemas import QuestionOrder, DecisionNode
from src.core.exceptions import TreeStructureError

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
        Given these clinical criteria, determine the optimal order for asking questions in a decision tree.
        Consider:
        1. Most exclusionary criteria first (likely to result in denial)
        2. Simple binary questions before complex ones
        3. Logical flow (diagnosis -> age -> prior therapy -> contraindications)
        4. Data collection at the end

        Criteria: {json.dumps(criteria, indent=2)}

        Return an ordered list of criterion IDs with reasoning for the order.
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
        
        Criterion: {json.dumps(criterion, indent=2)}
        
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
        # Placeholder for generating outcome nodes
        return []

    def _connect_nodes(self, nodes: list, parsed_criteria: dict) -> dict:
        # Placeholder for connecting nodes
        return {"nodes": nodes}
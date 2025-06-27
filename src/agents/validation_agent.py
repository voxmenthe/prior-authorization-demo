import json
from src.core.llm_client import LlmClient
from src.core.schemas import LogicalConsistencyCheck

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
            "suggestions": []
        }
        
        if self.verbose:
            node_count = len(tree.get('nodes', [])) if isinstance(tree, dict) else 0
            print(f"   Checking {node_count} nodes for logical consistency...")
        
        # Check for logical consistency
        logic_check = self._check_logical_consistency(tree)
        validation_results["issues"].extend(logic_check.get("issues", []))
        
        # Check for completeness
        completeness_check = self._check_completeness(tree)
        validation_results["issues"].extend(completeness_check.get("issues", []))
        
        # Check for ambiguity
        ambiguity_check = self._check_ambiguity(tree)
        validation_results["issues"].extend(ambiguity_check.get("issues", []))
        
        # Simulate edge cases
        edge_case_results = self._test_edge_cases(tree)
        validation_results["suggestions"].extend(edge_case_results.get("suggestions", []))
        
        validation_results["is_valid"] = len(validation_results["issues"]) == 0
        
        return validation_results
    
    def _check_logical_consistency(self, tree: dict) -> dict:
        prompt = f"""
        Analyze this decision tree for logical inconsistencies:
        
        Tree: {json.dumps(tree, indent=2)}
        
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
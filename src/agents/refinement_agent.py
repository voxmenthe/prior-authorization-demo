from src.core.llm_client import LlmClient
from src.core.schemas import RefinedTreeSection, KeyValuePair
from src.agents.conflict_resolver import ConflictResolver
from src.utils.json_utils import sanitize_json_for_prompt

class RefinementAgent:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.llm = LlmClient(verbose=verbose)
        self.conflict_resolver = ConflictResolver(verbose=verbose)
        if verbose:
            print("🔧 RefinementAgent initialized")
        
    def refine(self, tree: dict, validation_results: dict) -> dict:
        if self.verbose:
            print(f"\n🔧 Refining tree based on validation results")
            issues_count = len(validation_results.get("issues", []))
            suggestions_count = len(validation_results.get("suggestions", []))
            conflicts_count = len(validation_results.get("conflicts", []))
            print(f"   Issues to fix: {issues_count}")
            print(f"   Suggestions to implement: {suggestions_count}")
            print(f"   Conflicts to resolve: {conflicts_count}")
        
        refined_tree = tree.copy()
        
        # Resolve conflicts first (highest priority)
        conflicts = validation_results.get("conflicts", [])
        if conflicts:
            resolution_results = self.conflict_resolver.resolve_conflicts(refined_tree, conflicts)
            refined_tree = resolution_results['tree']
            
            if self.verbose and resolution_results['resolutions']:
                print(f"   ✓ Resolved {len(resolution_results['resolutions'])} conflicts")
            if self.verbose and resolution_results['unresolved']:
                print(f"   ⚠ Unable to resolve {len(resolution_results['unresolved'])} conflicts")
        
        # Fix identified issues
        for issue in validation_results.get("issues", []):
            refined_tree = self._fix_issue(refined_tree, issue)
        
        # Implement suggestions
        for suggestion in validation_results.get("suggestions", []):
            refined_tree = self._implement_suggestion(refined_tree, suggestion)
        
        # Optimize tree structure
        refined_tree = self._optimize_structure(refined_tree)
        
        # Add metadata
        refined_tree = self._add_metadata(refined_tree)
        
        return refined_tree
    
    def _fix_issue(self, tree: dict, issue: dict) -> dict:
        prompt = f"""
        Fix the following issue in the decision tree:
        
        Issue: {sanitize_json_for_prompt(issue)}
        Current tree section: {self._extract_relevant_section(tree, issue.get("node_ids", []))}
        
        Provide the corrected tree section that resolves this issue while maintaining
        clinical accuracy and logical flow.
        """
        
        correction = self.llm.generate_structured_json(
            prompt=prompt,
            response_schema=RefinedTreeSection
        )
        
        # Convert KeyValuePair list back to dict for merging
        correction_dict = KeyValuePair.to_dict(correction.corrected_section)
        return self._merge_correction(tree, correction_dict)

    def _extract_relevant_section(self, tree: dict, node_ids: list) -> str:
        """Extract relevant tree section without double JSON encoding."""
        if not node_ids:
            # Return a simplified representation instead of full JSON
            if isinstance(tree, dict) and "nodes" in tree:
                node_count = len(tree["nodes"])
                return f"Tree with {node_count} nodes"
            return "Full tree structure"
        
        # Extract specific nodes if node_ids provided
        relevant_nodes = {}
        if isinstance(tree, dict) and "nodes" in tree:
            for node_id in node_ids:
                if node_id in tree["nodes"]:
                    relevant_nodes[node_id] = tree["nodes"][node_id]
        
        if relevant_nodes:
            return f"Relevant nodes: {list(relevant_nodes.keys())}"
        return "No relevant nodes found"

    def _merge_correction(self, tree: dict, correction: dict) -> dict:
        # Placeholder for merging correction
        # This needs to be implemented based on how the tree structure is defined.
        # For now, we'll just return the correction if it's a complete tree.
        if "nodes" in correction:
            return correction
        return tree # Return original tree if correction is not a complete tree
    
    def _implement_suggestion(self, tree: dict, suggestion: dict) -> dict:
        # Placeholder for implementing suggestion
        return tree

    def _optimize_structure(self, tree: dict) -> dict:
        # Combine similar questions
        tree = self._combine_similar_nodes(tree)
        
        # Simplify complex branches
        tree = self._simplify_branches(tree)
        
        # Ensure all paths lead to outcomes
        tree = self._ensure_complete_paths(tree)
        
        return tree

    def _combine_similar_nodes(self, tree: dict) -> dict:
        # Placeholder for combining similar nodes
        return tree

    def _simplify_branches(self, tree: dict) -> dict:
        # Placeholder for simplifying branches
        return tree

    def _ensure_complete_paths(self, tree: dict) -> dict:
        # Placeholder for ensuring complete paths
        return tree

    def _add_metadata(self, tree: dict) -> dict:
        # Placeholder for adding metadata
        return tree
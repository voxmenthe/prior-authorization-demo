"""Centralized prompt template management for LLM operations."""

from typing import Dict, Any

# Validation agent prompts
VALIDATION_PROMPTS = {
    'logical_consistency': """
    Analyze this decision tree for logical inconsistencies:
    
    Tree: {tree}
    
    Check for:
    1. Contradictory paths (same condition leading to different outcomes)
    2. Circular dependencies (nodes that form loops)
    3. Unreachable nodes (nodes with no incoming connections except start_node)
    4. Missing decision paths (decision nodes with no outgoing connections)
    5. Incorrect boolean logic
    
    Return any issues found with specific node IDs and explanations.
    """,
    
    'completeness': """
    Analyze if this decision tree covers all medical criteria comprehensively:
    
    Tree: {tree}
    Original Criteria Count: {criteria_count}
    
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
    """,
    
    'ambiguity': """
    Analyze this decision tree for ambiguous or unclear language:
    
    Tree: {tree}
    
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
}

# Tree structure agent prompts
TREE_STRUCTURE_PROMPTS = {
    'question_order': """
    Given these clinical criteria, determine the optimal order for asking questions in a decision tree 
    that leads to efficient APPROVE/DENY decisions.

    Consider:
    1. Most exclusionary criteria first (likely to result in DENIAL - fail fast)
    2. Expensive/complex checks last (only if cheaper checks pass)
    3. Logical medical workflow (diagnosis -> eligibility -> contraindications -> documentation)
    4. Group related criteria to minimize cognitive load
    5. Put documentation requirements at the end (assuming clinical criteria pass)

    Criteria: {criteria}

    IMPORTANT: Order criteria to minimize total questions needed for most common denial reasons.
    Exclusionary criteria should be checked before inclusionary criteria when possible.

    Return an ordered list of criterion IDs with reasoning for the order that optimizes for 
    both user experience and processing efficiency.
    """,
    
    'create_node': """
    Convert this clinical criterion into a decision tree node question.
    
    Criterion: {criterion}
    
    Guidelines:
    1. Make the question clear and unambiguous
    2. Use medical terminology appropriately but include help text
    3. Specify the expected answer format (yes/no, multiple choice, numeric)
    4. Include validation rules for data entry
    
    Return a JSON node structure with id '{node_id}'.
    """,
    
    'connect_nodes': """
    Connect these decision tree nodes with proper logic flow to reach APPROVE/DENY decisions:
    
    Nodes: {nodes}
    Criteria: {criteria}
    
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
}

# Criteria parser agent prompts
CRITERIA_PARSER_PROMPTS = {
    'parse_criteria': """
    You are a medical criteria parser. Extract all approval criteria from the following text.
    
    Focus on:
    1. Clinical requirements (diagnoses, test results, thresholds)
    2. Patient eligibility criteria (age, condition severity, prior treatments)
    3. Documentation requirements
    4. Exclusionary conditions
    5. Time-based requirements (duration of condition, trial periods)
    
    Text: {text}
    
    Structure each criterion with:
    - Unique ID
    - Type (REQUIRED, EXCLUSIONARY, THRESHOLD, DOCUMENTATION)
    - Clear condition statement
    - Parameters (thresholds, operators, units)
    - Sub-conditions if applicable
    - Exceptions or special cases
    """
}

# Refinement agent prompts
REFINEMENT_PROMPTS = {
    'refine_tree': """
    Refine this decision tree based on validation feedback:
    
    Tree: {tree}
    Validation Issues: {issues}
    
    For each issue:
    1. Understand the root cause
    2. Propose a specific fix
    3. Ensure the fix doesn't create new issues
    4. Maintain logical consistency
    
    Return the refined tree with all issues addressed.
    """,
    
    'add_missing_criteria': """
    Add missing criteria to the decision tree:
    
    Current Tree: {tree}
    Missing Criteria: {missing_criteria}
    
    For each missing criterion:
    1. Determine the optimal position in the tree
    2. Create appropriate decision nodes
    3. Connect to existing flow
    4. Ensure no contradictions
    
    Return the updated tree structure.
    """
}

# Conflict resolution prompts (for future enhancement)
CONFLICT_RESOLUTION_PROMPTS = {
    'resolve_contradictions': """
    Resolve contradictory paths in the decision tree:
    
    Tree: {tree}
    Conflicts: {conflicts}
    
    For each conflict:
    1. Identify the root cause of contradiction
    2. Determine which path is medically correct
    3. Propose resolution that maintains consistency
    4. Ensure no new conflicts are introduced
    
    Return resolution suggestions with confidence scores.
    """,
    
    'merge_criteria': """
    Merge related criteria from multiple documents:
    
    Primary Criteria: {primary}
    Secondary Criteria: {secondary}
    
    Rules:
    1. Primary document takes precedence
    2. Identify complementary vs. contradictory criteria
    3. Merge complementary criteria
    4. Flag contradictions for review
    
    Return merged criteria with source attribution.
    """
}


class PromptTemplateManager:
    """Manages and formats prompt templates for LLM operations."""
    
    def __init__(self):
        self.templates = {
            'validation': VALIDATION_PROMPTS,
            'tree_structure': TREE_STRUCTURE_PROMPTS,
            'criteria_parser': CRITERIA_PARSER_PROMPTS,
            'refinement': REFINEMENT_PROMPTS,
            'conflict_resolution': CONFLICT_RESOLUTION_PROMPTS
        }
    
    def get_prompt(self, category: str, template_name: str, **kwargs) -> str:
        """
        Get a formatted prompt template.
        
        Args:
            category: The category of prompts (e.g., 'validation', 'tree_structure')
            template_name: The specific template name within the category
            **kwargs: Variables to format into the template
            
        Returns:
            Formatted prompt string
            
        Raises:
            KeyError: If category or template_name not found
        """
        if category not in self.templates:
            raise KeyError(f"Prompt category '{category}' not found. Available: {list(self.templates.keys())}")
            
        category_templates = self.templates[category]
        
        if template_name not in category_templates:
            raise KeyError(f"Template '{template_name}' not found in category '{category}'. Available: {list(category_templates.keys())}")
            
        template = category_templates[template_name]
        
        try:
            return template.format(**kwargs)
        except KeyError as e:
            raise KeyError(f"Missing required variable for template '{template_name}': {e}")
    
    def add_template(self, category: str, template_name: str, template: str):
        """Add a new template to the manager."""
        if category not in self.templates:
            self.templates[category] = {}
        
        self.templates[category][template_name] = template
    
    def list_templates(self, category: str = None) -> Dict[str, list]:
        """List available templates, optionally filtered by category."""
        if category:
            if category in self.templates:
                return {category: list(self.templates[category].keys())}
            else:
                return {}
        
        return {cat: list(templates.keys()) for cat, templates in self.templates.items()}


# Singleton instance for easy import
prompt_manager = PromptTemplateManager()
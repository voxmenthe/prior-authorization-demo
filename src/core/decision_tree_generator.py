from src.core.llm_client import LlmClient
from src.agents.criteria_parser_agent import CriteriaParserAgent
from src.agents.tree_structure_agent import TreeStructureAgent
from src.agents.validation_agent import ValidationAgent
from src.agents.refinement_agent import RefinementAgent

class DecisionTreeGenerator:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.llm_client = LlmClient(verbose=verbose)
        self.parser_agent = CriteriaParserAgent(verbose=verbose)
        self.structure_agent = TreeStructureAgent(verbose=verbose)
        self.validation_agent = ValidationAgent(verbose=verbose)
        self.refinement_agent = RefinementAgent(verbose=verbose)
        
        if verbose:
            print("🏭 DecisionTreeGenerator initialized with all agents")
        
    def generate_decision_tree(self, ocr_text: str) -> dict:
        if self.verbose:
            print("\n🚀 Starting decision tree generation pipeline")
        
        # Step 1: Parse and structure the criteria
        if self.verbose:
            print("\n📋 Step 1: Parsing criteria...")
        parsed_criteria = self.parser_agent.parse(ocr_text)
        
        # Step 2: Extract decision points and create initial tree
        if self.verbose:
            print("\n🌳 Step 2: Creating tree structure...")
        initial_tree = self.structure_agent.create_tree(parsed_criteria)
        
        # Step 3: Validate logical consistency
        if self.verbose:
            print("\n✅ Step 3: Validating tree...")
        validation_results = self.validation_agent.validate(initial_tree)
        
        # Step 4: Refine based on validation feedback
        if self.verbose:
            print("\n🔧 Step 4: Refining tree...")
        final_tree = self.refinement_agent.refine(initial_tree, validation_results)
        
        if self.verbose:
            print("\n🎉 Decision tree generation complete!")
        
        return final_tree

from typing import Optional, Union, List
from pathlib import Path
from src.core.llm_client import LlmClient
from src.agents.criteria_parser_agent import CriteriaParserAgent
from src.agents.tree_structure_agent import TreeStructureAgent
from src.agents.validation_agent import ValidationAgent
from src.agents.refinement_agent import RefinementAgent
from src.core.config import get_config
from src.core.schemas import DocumentSet, UnifiedDecisionTree
from src.utils.document_set_manager import DocumentSetManager

class DecisionTreeGenerator:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.llm_client = LlmClient(verbose=verbose)
        self.parser_agent = CriteriaParserAgent(verbose=verbose)
        self.structure_agent = TreeStructureAgent(verbose=verbose)
        self.validation_agent = ValidationAgent(verbose=verbose)
        self.refinement_agent = RefinementAgent(verbose=verbose)
        
        # Multi-document support
        self.config = get_config()
        self.document_set_manager = DocumentSetManager()
        self.multi_doc_adapter = None  # Lazy initialization to avoid circular dependency
        
        if verbose:
            print("🏭 DecisionTreeGenerator initialized with all agents")
            if self.config.enable_multi_document:
                print("📚 Multi-document processing enabled")
        
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
        
    def generate_from_documents(self, document_paths: Union[str, Path, List[Union[str, Path]]]) -> Union[dict, UnifiedDecisionTree]:
        """
        Generate decision tree from one or more documents.
        
        Args:
            document_paths: Single document path or list of document paths
            
        Returns:
            For single document: dict with decision tree
            For multiple documents with multi-doc enabled: UnifiedDecisionTree
            For multiple documents without multi-doc: dict from primary document
        """
        # Convert to list of Path objects
        if isinstance(document_paths, (str, Path)):
            paths = [Path(document_paths)]
        else:
            paths = [Path(p) for p in document_paths]
            
        # Single document case
        if len(paths) == 1:
            with open(paths[0], 'r', encoding='utf-8') as f:
                content = f.read()
            return self.generate_decision_tree(content)
            
        # Multiple documents
        if self.config.enable_multi_document:
            if self.verbose:
                print("\n📚 Processing multiple documents with multi-document support")
                
            # Initialize adapter if needed (lazy import to avoid circular dependency)
            if self.multi_doc_adapter is None:
                from src.adapters.multi_document_adapter import MultiDocumentAdapter
                self.multi_doc_adapter = MultiDocumentAdapter(self)
                
            # Identify document set
            doc_set = self.document_set_manager.identify_document_set(paths)
            
            if doc_set is None:
                if self.verbose:
                    print("⚠️  Could not identify document relationships, processing primary document only")
                # Fall back to single document processing
                with open(paths[0], 'r', encoding='utf-8') as f:
                    content = f.read()
                return self.generate_decision_tree(content)
                
            # Process document set
            return self.multi_doc_adapter.process_document_set(doc_set)
            
        else:
            # Multi-document disabled, process only the first document
            if self.verbose:
                print("\n⚠️  Multiple documents provided but multi-document processing is disabled")
                print("   Processing only the first document")
                
            with open(paths[0], 'r', encoding='utf-8') as f:
                content = f.read()
            return self.generate_decision_tree(content)
            
    def process_document_set(self, doc_set: DocumentSet) -> UnifiedDecisionTree:
        """
        Process a pre-identified document set.
        
        Args:
            doc_set: DocumentSet object with document relationships
            
        Returns:
            UnifiedDecisionTree with merged criteria
        """
        if not self.config.enable_multi_document:
            raise ValueError("Multi-document processing is not enabled. Set ENABLE_MULTI_DOCUMENT=true")
            
        # Initialize adapter if needed (lazy import to avoid circular dependency)
        if self.multi_doc_adapter is None:
            from src.adapters.multi_document_adapter import MultiDocumentAdapter
            self.multi_doc_adapter = MultiDocumentAdapter(self)
            
        return self.multi_doc_adapter.process_document_set(doc_set)

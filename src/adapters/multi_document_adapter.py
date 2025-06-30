from typing import Dict, List, Optional, Any
from pathlib import Path
import copy
from src.core.schemas import DocumentSet, UnifiedDecisionTree
from src.core.decision_tree_generator import DecisionTreeGenerator


class MultiDocumentAdapter:
    """Adapts single-document pipeline for multi-document processing"""
    
    def __init__(self, generator: DecisionTreeGenerator):
        self.generator = generator
        self.cache = {}
        
    def process_document_set(self, doc_set: DocumentSet) -> UnifiedDecisionTree:
        """Process a document set - Phase 1: Simple merge without reference resolution"""
        
        # Step 1: Process primary document
        primary_result = self._process_primary(doc_set)
        
        # Step 2: Process supplementary documents
        supplementary_results = self._process_supplementary_docs(doc_set)
        
        # Step 3: Simple merge (no reference resolution yet)
        unified_tree = self._simple_merge(primary_result, supplementary_results, doc_set)
        
        return unified_tree
        
    def _process_primary(self, doc_set: DocumentSet) -> dict:
        """Process primary document through existing pipeline"""
        primary_metadata = doc_set.documents[doc_set.primary_document_id]
        primary_path = Path(primary_metadata.file_path)
        
        # Load document content
        with open(primary_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Use existing single-document pipeline
        result = self.generator.generate_decision_tree(content)
        
        # Enhance with multi-doc metadata
        if 'metadata' not in result:
            result['metadata'] = {}
        result['metadata']['document_set_id'] = doc_set.set_id
        result['metadata']['document_role'] = 'primary'
        result['metadata']['document_id'] = doc_set.primary_document_id
        
        # Store the full result with parsed criteria
        enhanced_result = {
            'decision_tree': result,
            'parsed_criteria': self._extract_criteria_from_tree(result),
            'document_id': doc_set.primary_document_id,
            'metadata': result.get('metadata', {})
        }
        
        # Cache the result
        self.cache[doc_set.primary_document_id] = enhanced_result
        
        return enhanced_result
        
    def _process_supplementary_docs(self, doc_set: DocumentSet) -> Dict[str, dict]:
        """Process all supplementary documents"""
        results = {}
        
        for doc_id, metadata in doc_set.documents.items():
            if doc_id == doc_set.primary_document_id:
                continue
                
            doc_path = Path(metadata.file_path)
            
            # Load document content
            with open(doc_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            result = self.generator.generate_decision_tree(content)
            
            # Enhance with metadata
            if 'metadata' not in result:
                result['metadata'] = {}
            result['metadata']['document_set_id'] = doc_set.set_id
            result['metadata']['document_role'] = 'supplementary'
            result['metadata']['document_id'] = doc_id
            
            # Store enhanced result
            enhanced_result = {
                'decision_tree': result,
                'parsed_criteria': self._extract_criteria_from_tree(result),
                'document_id': doc_id,
                'metadata': result.get('metadata', {})
            }
            
            results[doc_id] = enhanced_result
            self.cache[doc_id] = enhanced_result
            
        return results
        
    def _simple_merge(self, primary_result: dict, 
                      supplementary_results: Dict[str, dict],
                      doc_set: DocumentSet) -> UnifiedDecisionTree:
        """Simple merge strategy - append supplementary criteria to primary tree"""
        
        # Deep copy primary tree as base
        merged_tree = copy.deepcopy(primary_result.get('decision_tree', {}))
        
        # Collect all criteria from supplementary documents
        supplementary_criteria = []
        for doc_id, result in supplementary_results.items():
            criteria = result.get('parsed_criteria', [])
            for criterion in criteria:
                # Add source attribution
                criterion_copy = copy.deepcopy(criterion)
                criterion_copy['source_document'] = doc_id
                supplementary_criteria.append(criterion_copy)
                    
        # Add supplementary criteria as additional nodes
        if supplementary_criteria:
            # Create a supplementary criteria section
            supplementary_section = {
                'type': 'criteria_group',
                'title': 'Additional Criteria from Supplementary Documents',
                'description': 'These criteria are derived from clinical guidelines and supplementary documents',
                'criteria': supplementary_criteria,
                'source_documents': list(supplementary_results.keys())
            }
            
            # Add to the tree structure
            if 'supplementary_sections' not in merged_tree:
                merged_tree['supplementary_sections'] = []
            merged_tree['supplementary_sections'].append(supplementary_section)
            
        # Add merge metadata
        if 'metadata' not in merged_tree:
            merged_tree['metadata'] = {}
            
        merged_tree['metadata']['merge_strategy'] = 'simple_append'
        merged_tree['metadata']['document_count'] = len(doc_set.documents)
        merged_tree['metadata']['primary_document'] = doc_set.primary_document_id
        merged_tree['metadata']['supplementary_documents'] = list(supplementary_results.keys())
        
        # Create UnifiedDecisionTree
        unified_tree = UnifiedDecisionTree(
            tree=merged_tree,
            source_documents=[doc_set.primary_document_id] + list(supplementary_results.keys()),
            metadata={
                'document_set_id': doc_set.set_id,
                'merge_strategy': 'simple_append',
                'processing_metadata': doc_set.processing_metadata,
                'relationships': [
                    {
                        'from_doc': rel.from_doc,
                        'to_doc': rel.to_doc,
                        'type': rel.relationship_type.value
                    }
                    for rel in doc_set.relationships
                ]
            },
            extracted_references=[],  # For future use
            resolved_references_count=0  # For future use
        )
        
        return unified_tree
        
    def _extract_criteria_from_tree(self, tree: dict) -> List[dict]:
        """Extract criteria from a decision tree structure"""
        criteria = []
        
        # This is a simplified extraction - in reality, we'd parse the tree structure
        # to extract all criteria nodes
        if isinstance(tree, dict):
            # Look for criteria in various possible locations
            if 'criteria' in tree:
                criteria.extend(tree['criteria'])
            if 'nodes' in tree:
                for node in tree['nodes']:
                    if isinstance(node, dict) and 'criteria' in node:
                        criteria.extend(node['criteria'])
            if 'decision_points' in tree:
                for point in tree['decision_points']:
                    if isinstance(point, dict) and 'criteria' in point:
                        criteria.extend(point['criteria'])
                        
        return criteria
        
    def clear_cache(self):
        """Clear the document processing cache"""
        self.cache.clear()
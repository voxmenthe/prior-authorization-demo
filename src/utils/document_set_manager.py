from pathlib import Path
from typing import List, Optional, Union, Tuple
import json
import re
import uuid
from src.core.schemas import (
    DocumentSet, 
    DocumentMetadata, 
    DocumentRelationship, 
    DocumentRelationType
)


class DocumentSetManager:
    """Manages identification and grouping of related documents"""
    
    def __init__(self):
        self.pattern_matchers = [
            # Pattern: {drug_name}_{doc_type}.txt
            (r'^(.+?)_(insurance|policy|guidelines|clinical)\.txt$', 'underscore'),
            # Pattern: {drug_name}-{doc_type}.txt
            (r'^(.+?)-(insurance|policy|guidelines|clinical)\.txt$', 'dash'),
        ]
        
    def identify_document_set(self, paths: Union[Path, List[Path]]) -> Optional[DocumentSet]:
        """Identify if paths constitute a document set"""
        if isinstance(paths, Path):
            return None  # Single document, no set
            
        if len(paths) < 2:
            return None
            
        # Check for manifest file first
        manifest = self._find_manifest(paths)
        if manifest:
            return self._load_from_manifest(manifest)
            
        # Try pattern-based grouping
        return self._group_by_patterns(paths)
        
    def _find_manifest(self, paths: List[Path]) -> Optional[Path]:
        """Look for manifest.json in the directory"""
        if paths:
            parent = paths[0].parent
            manifest_path = parent / "manifest.json"
            if manifest_path.exists():
                return manifest_path
        return None
        
    def _load_from_manifest(self, manifest_path: Path) -> DocumentSet:
        """Load document set from manifest file"""
        with open(manifest_path, 'r') as f:
            data = json.load(f)
        
        # Convert to DocumentSet
        documents = {}
        for doc_id, doc_data in data.get('documents', {}).items():
            documents[doc_id] = DocumentMetadata(**doc_data)
            
        relationships = []
        for rel_data in data.get('relationships', []):
            rel_type = DocumentRelationType(rel_data['relationship_type'])
            relationships.append(DocumentRelationship(
                from_doc=rel_data['from_doc'],
                to_doc=rel_data['to_doc'],
                relationship_type=rel_type,
                references=rel_data.get('references', [])
            ))
            
        return DocumentSet(
            set_id=data.get('set_id', str(uuid.uuid4())),
            primary_document_id=data['primary_document_id'],
            documents=documents,
            relationships=relationships,
            processing_metadata=data.get('processing_metadata', {})
        )
        
    def _group_by_patterns(self, paths: List[Path]) -> Optional[DocumentSet]:
        """Group documents by naming patterns"""
        # Group files by base name
        groups = {}
        
        for path in paths:
            filename = path.name
            
            for pattern, pattern_type in self.pattern_matchers:
                match = re.match(pattern, filename)
                if match:
                    base_name = match.group(1)
                    doc_type = match.group(2)
                    
                    # Handle compound document types (e.g., "dupixent_insurance_policy.txt")
                    # Check if base_name ends with a document type word
                    for dtype in ['insurance', 'clinical', 'policy', 'guidelines']:
                        if base_name.endswith(f'_{dtype}'):
                            base_name = base_name[:-len(f'_{dtype}')]
                            doc_type = f"{dtype}_{doc_type}"  # Combine the full type
                            break
                    
                    if base_name not in groups:
                        groups[base_name] = []
                    groups[base_name].append((path, doc_type))
                    break
        
        # Find the largest group
        if not groups:
            return None
            
        largest_group_key = max(groups.keys(), key=lambda k: len(groups[k]))
        largest_group = groups[largest_group_key]
        
        if len(largest_group) < 2:
            return None
            
        # Create DocumentSet from the largest group
        documents = {}
        relationships = []
        primary_doc_id = None
        
        for i, (path, doc_type) in enumerate(largest_group):
            doc_id = f"{largest_group_key}_{doc_type}"
            documents[doc_id] = DocumentMetadata(
                file_path=str(path),
                document_id=doc_id,
                source=path.parent.name,
                document_type=doc_type
            )
            
            # Set primary document (prefer insurance/policy)
            if doc_type in ['insurance', 'policy'] and primary_doc_id is None:
                primary_doc_id = doc_id
            elif i == 0 and primary_doc_id is None:
                primary_doc_id = doc_id
                
        # Create relationships between insurance and guidelines
        insurance_docs = [d for d in documents.keys() if 'insurance' in d or 'policy' in d]
        guidelines_docs = [d for d in documents.keys() if 'guidelines' in d or 'clinical' in d]
        
        for ins_doc in insurance_docs:
            for guide_doc in guidelines_docs:
                relationships.append(DocumentRelationship(
                    from_doc=ins_doc,
                    to_doc=guide_doc,
                    relationship_type=DocumentRelationType.CROSS_REFERENCED
                ))
                
        return DocumentSet(
            set_id=f"{largest_group_key}_set_{uuid.uuid4().hex[:8]}",
            primary_document_id=primary_doc_id,
            documents=documents,
            relationships=relationships,
            processing_metadata={"grouping_method": "pattern_matching"}
        )
        
    def create_manifest(self, doc_set: DocumentSet, output_path: Path) -> None:
        """Save a DocumentSet as a manifest file"""
        manifest_data = {
            "set_id": doc_set.set_id,
            "primary_document_id": doc_set.primary_document_id,
            "documents": {
                doc_id: {
                    "file_path": doc.file_path,
                    "document_id": doc.document_id,
                    "source": doc.source,
                    "document_type": doc.document_type,
                    "effective_date": doc.effective_date
                }
                for doc_id, doc in doc_set.documents.items()
            },
            "relationships": [
                {
                    "from_doc": rel.from_doc,
                    "to_doc": rel.to_doc,
                    "relationship_type": rel.relationship_type.value,
                    "references": rel.references
                }
                for rel in doc_set.relationships
            ],
            "processing_metadata": doc_set.processing_metadata
        }
        
        with open(output_path, 'w') as f:
            json.dump(manifest_data, f, indent=2)
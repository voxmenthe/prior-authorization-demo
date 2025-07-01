"""Tests for DocumentSetManager"""

import pytest
from pathlib import Path
import json
import tempfile
import shutil
from src.utils.document_set_manager import DocumentSetManager
from src.core.schemas import DocumentSet, DocumentMetadata, DocumentRelationship, DocumentRelationType


class TestDocumentSetManager:
    """Test cases for DocumentSetManager"""
    
    @pytest.fixture
    def manager(self):
        """Create a DocumentSetManager instance"""
        return DocumentSetManager()
        
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files"""
        temp_path = tempfile.mkdtemp()
        yield Path(temp_path)
        shutil.rmtree(temp_path)
        
    def test_single_document_returns_none(self, manager):
        """Test that single document returns None"""
        result = manager.identify_document_set(Path("test.txt"))
        assert result is None
        
    def test_single_document_list_returns_none(self, manager):
        """Test that list with single document returns None"""
        result = manager.identify_document_set([Path("test.txt")])
        assert result is None
        
    def test_pattern_matching_underscore(self, manager, temp_dir):
        """Test pattern matching with underscore separator"""
        # Create test files
        files = [
            temp_dir / "dupixent_insurance.txt",
            temp_dir / "dupixent_guidelines.txt"
        ]
        for f in files:
            f.write_text("test content")
            
        doc_set = manager.identify_document_set(files)
        
        assert doc_set is not None
        assert len(doc_set.documents) == 2
        assert "dupixent_insurance" in doc_set.documents
        assert "dupixent_guidelines" in doc_set.documents
        assert doc_set.primary_document_id == "dupixent_insurance"
        
    def test_pattern_matching_dash(self, manager, temp_dir):
        """Test pattern matching with dash separator"""
        files = [
            temp_dir / "humira-policy.txt",
            temp_dir / "humira-clinical.txt"
        ]
        for f in files:
            f.write_text("test content")
            
        doc_set = manager.identify_document_set(files)
        
        assert doc_set is not None
        assert len(doc_set.documents) == 2
        assert "humira_policy" in doc_set.documents
        assert "humira_clinical" in doc_set.documents
        
    def test_manifest_loading(self, manager, temp_dir):
        """Test loading document set from manifest"""
        # Create manifest
        manifest_data = {
            "set_id": "test_set_001",
            "primary_document_id": "main_doc",
            "documents": {
                "main_doc": {
                    "file_path": str(temp_dir / "main.txt"),
                    "document_id": "main_doc",
                    "source": "test",
                    "document_type": "insurance",
                    "effective_date": "2024-01-01"
                },
                "supp_doc": {
                    "file_path": str(temp_dir / "supplement.txt"),
                    "document_id": "supp_doc",
                    "source": "test",
                    "document_type": "guidelines",
                    "effective_date": None
                }
            },
            "relationships": [
                {
                    "from_doc": "main_doc",
                    "to_doc": "supp_doc",
                    "relationship_type": "cross_referenced",
                    "references": ["section_1", "section_2"]
                }
            ],
            "processing_metadata": {"test": "value"}
        }
        
        manifest_path = temp_dir / "manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest_data, f)
            
        # Create dummy files
        (temp_dir / "main.txt").write_text("main content")
        (temp_dir / "supplement.txt").write_text("supplement content")
        
        # Test loading
        doc_set = manager.identify_document_set([
            temp_dir / "main.txt",
            temp_dir / "supplement.txt"
        ])
        
        assert doc_set is not None
        assert doc_set.set_id == "test_set_001"
        assert doc_set.primary_document_id == "main_doc"
        assert len(doc_set.documents) == 2
        assert len(doc_set.relationships) == 1
        assert doc_set.relationships[0].relationship_type == DocumentRelationType.CROSS_REFERENCED
        
    def test_create_manifest(self, manager, temp_dir):
        """Test creating a manifest from a DocumentSet"""
        # Create a document set
        doc_set = DocumentSet(
            set_id="test_creation",
            primary_document_id="doc1",
            documents={
                "doc1": DocumentMetadata(
                    file_path="/path/to/doc1.txt",
                    document_id="doc1",
                    source="test",
                    document_type="insurance"
                ),
                "doc2": DocumentMetadata(
                    file_path="/path/to/doc2.txt",
                    document_id="doc2",
                    source="test",
                    document_type="guidelines"
                )
            },
            relationships=[
                DocumentRelationship(
                    from_doc="doc1",
                    to_doc="doc2",
                    relationship_type=DocumentRelationType.PRIMARY_SUPPLEMENTARY
                )
            ]
        )
        
        # Save manifest
        manifest_path = temp_dir / "output_manifest.json"
        manager.create_manifest(doc_set, manifest_path)
        
        # Verify manifest was created correctly
        assert manifest_path.exists()
        
        with open(manifest_path, 'r') as f:
            loaded_data = json.load(f)
            
        assert loaded_data["set_id"] == "test_creation"
        assert loaded_data["primary_document_id"] == "doc1"
        assert len(loaded_data["documents"]) == 2
        assert len(loaded_data["relationships"]) == 1
        
    def test_mixed_patterns_not_matched(self, manager, temp_dir):
        """Test that files with different patterns are not grouped"""
        files = [
            temp_dir / "dupixent_insurance.txt",
            temp_dir / "humira-guidelines.txt",
            temp_dir / "other_document.pdf"
        ]
        for f in files:
            f.write_text("test content")
            
        doc_set = manager.identify_document_set(files)
        
        # Should return None or a set with only matching files
        assert doc_set is None
        
    def test_relationship_creation(self, manager, temp_dir):
        """Test that relationships are created correctly"""
        files = [
            temp_dir / "drug_insurance.txt",
            temp_dir / "drug_guidelines.txt",
            temp_dir / "drug_clinical.txt"
        ]
        for f in files:
            f.write_text("test content")
            
        doc_set = manager.identify_document_set(files)
        
        assert doc_set is not None
        
        # Check relationships
        insurance_to_guidelines = False
        insurance_to_clinical = False
        
        for rel in doc_set.relationships:
            if "insurance" in rel.from_doc:
                if "guidelines" in rel.to_doc:
                    insurance_to_guidelines = True
                elif "clinical" in rel.to_doc:
                    insurance_to_clinical = True
                    
        assert insurance_to_guidelines
        assert insurance_to_clinical
        
    def test_no_matching_patterns(self, manager, temp_dir):
        """Test files with no matching patterns"""
        files = [
            temp_dir / "random1.txt",
            temp_dir / "random2.txt"
        ]
        for f in files:
            f.write_text("test content")
            
        doc_set = manager.identify_document_set(files)
        assert doc_set is None
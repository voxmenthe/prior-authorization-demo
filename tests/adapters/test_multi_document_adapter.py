"""Tests for MultiDocumentAdapter"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path
import tempfile
import shutil

from src.adapters.multi_document_adapter import MultiDocumentAdapter
from src.core.schemas import (
    DocumentSet, 
    DocumentMetadata, 
    DocumentRelationship, 
    DocumentRelationType,
    UnifiedDecisionTree
)
from src.core.decision_tree_generator import DecisionTreeGenerator


class TestMultiDocumentAdapter:
    """Test cases for MultiDocumentAdapter"""
    
    @pytest.fixture
    def mock_generator(self):
        """Create a mock DecisionTreeGenerator"""
        generator = Mock(spec=DecisionTreeGenerator)
        generator.generate_decision_tree = Mock(return_value={
            "tree_type": "decision",
            "nodes": [
                {
                    "id": "node1",
                    "type": "decision",
                    "question": "Is the patient 18 or older?",
                    "yes_path": "node2",
                    "no_path": "reject"
                }
            ],
            "criteria": [
                {"id": "c1", "description": "Age requirement"}
            ]
        })
        return generator
        
    @pytest.fixture
    def adapter(self, mock_generator):
        """Create a MultiDocumentAdapter instance"""
        return MultiDocumentAdapter(mock_generator)
        
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files"""
        temp_path = tempfile.mkdtemp()
        yield Path(temp_path)
        shutil.rmtree(temp_path)
        
    @pytest.fixture
    def sample_doc_set(self, temp_dir):
        """Create a sample DocumentSet"""
        # Create test files
        primary_file = temp_dir / "insurance.txt"
        primary_file.write_text("Insurance criteria: Age 18+, Prior auth required")
        
        supp_file = temp_dir / "guidelines.txt"
        supp_file.write_text("Clinical guidelines: Try step therapy first")
        
        return DocumentSet(
            set_id="test_set_001",
            primary_document_id="insurance_doc",
            documents={
                "insurance_doc": DocumentMetadata(
                    file_path=str(primary_file),
                    document_id="insurance_doc",
                    source="test",
                    document_type="insurance"
                ),
                "guidelines_doc": DocumentMetadata(
                    file_path=str(supp_file),
                    document_id="guidelines_doc",
                    source="test",
                    document_type="guidelines"
                )
            },
            relationships=[
                DocumentRelationship(
                    from_doc="insurance_doc",
                    to_doc="guidelines_doc",
                    relationship_type=DocumentRelationType.CROSS_REFERENCED
                )
            ]
        )
        
    def test_process_document_set(self, adapter, sample_doc_set):
        """Test basic document set processing"""
        result = adapter.process_document_set(sample_doc_set)
        
        assert isinstance(result, UnifiedDecisionTree)
        assert len(result.source_documents) == 2
        assert "insurance_doc" in result.source_documents
        assert "guidelines_doc" in result.source_documents
        assert result.metadata["document_set_id"] == "test_set_001"
        
    def test_process_primary_document(self, adapter, sample_doc_set):
        """Test processing of primary document"""
        result = adapter._process_primary(sample_doc_set)
        
        assert isinstance(result, dict)
        assert result["document_id"] == "insurance_doc"
        assert "decision_tree" in result
        assert "parsed_criteria" in result
        assert result["metadata"]["document_role"] == "primary"
        
    def test_process_supplementary_documents(self, adapter, sample_doc_set):
        """Test processing of supplementary documents"""
        # Process primary first to set up cache
        adapter._process_primary(sample_doc_set)
        
        results = adapter._process_supplementary_docs(sample_doc_set)
        
        assert len(results) == 1
        assert "guidelines_doc" in results
        assert results["guidelines_doc"]["metadata"]["document_role"] == "supplementary"
        
    def test_simple_merge_strategy(self, adapter, sample_doc_set):
        """Test the simple merge strategy"""
        # Create mock results
        primary_result = {
            "decision_tree": {
                "tree_type": "primary",
                "nodes": [{"id": "p1", "type": "decision"}],
                "criteria": [{"id": "pc1", "desc": "primary criterion"}]
            },
            "parsed_criteria": [{"id": "pc1", "desc": "primary criterion"}],
            "document_id": "insurance_doc",
            "metadata": {}
        }
        
        supplementary_results = {
            "guidelines_doc": {
                "decision_tree": {
                    "tree_type": "supplementary",
                    "nodes": [{"id": "s1", "type": "decision"}]
                },
                "parsed_criteria": [{"id": "sc1", "desc": "supplementary criterion"}],
                "document_id": "guidelines_doc",
                "metadata": {}
            }
        }
        
        unified = adapter._simple_merge(primary_result, supplementary_results, sample_doc_set)
        
        assert isinstance(unified, UnifiedDecisionTree)
        assert unified.tree["tree_type"] == "primary"  # Should keep primary structure
        assert "supplementary_sections" in unified.tree
        assert len(unified.tree["supplementary_sections"]) == 1
        assert unified.tree["supplementary_sections"][0]["type"] == "criteria_group"
        
    def test_extract_criteria_from_tree(self, adapter):
        """Test criteria extraction from tree structure"""
        tree = {
            "criteria": [{"id": "c1", "desc": "top level"}],
            "nodes": [
                {
                    "id": "n1",
                    "criteria": [{"id": "c2", "desc": "in node"}]
                }
            ],
            "decision_points": [
                {
                    "id": "dp1",
                    "criteria": [{"id": "c3", "desc": "in decision point"}]
                }
            ]
        }
        
        criteria = adapter._extract_criteria_from_tree(tree)
        
        assert len(criteria) == 3
        assert any(c["id"] == "c1" for c in criteria)
        assert any(c["id"] == "c2" for c in criteria)
        assert any(c["id"] == "c3" for c in criteria)
        
    def test_cache_functionality(self, adapter, sample_doc_set):
        """Test that results are cached"""
        # Process document set
        adapter.process_document_set(sample_doc_set)
        
        # Check cache
        assert len(adapter.cache) == 2
        assert "insurance_doc" in adapter.cache
        assert "guidelines_doc" in adapter.cache
        
        # Clear cache
        adapter.clear_cache()
        assert len(adapter.cache) == 0
        
    def test_metadata_enhancement(self, adapter, sample_doc_set):
        """Test that metadata is properly enhanced"""
        result = adapter.process_document_set(sample_doc_set)
        
        # Check tree metadata
        tree_metadata = result.tree.get("metadata", {})
        assert tree_metadata["merge_strategy"] == "simple_append"
        assert tree_metadata["document_count"] == 2
        assert tree_metadata["primary_document"] == "insurance_doc"
        
        # Check result metadata
        assert result.metadata["merge_strategy"] == "simple_append"
        assert len(result.metadata["relationships"]) == 1
        
    def test_empty_supplementary_criteria(self, adapter, sample_doc_set, mock_generator):
        """Test handling when supplementary documents have no criteria"""
        # Mock generator to return empty criteria for supplementary doc
        def side_effect(content):
            if "Clinical guidelines" in content:
                return {"tree_type": "empty", "nodes": []}
            return {
                "tree_type": "decision",
                "nodes": [{"id": "node1"}],
                "criteria": [{"id": "c1"}]
            }
            
        mock_generator.generate_decision_tree.side_effect = side_effect
        
        result = adapter.process_document_set(sample_doc_set)
        
        # Should still process successfully
        assert isinstance(result, UnifiedDecisionTree)
        assert len(result.source_documents) == 2
        
    def test_file_not_found_handling(self, adapter):
        """Test handling of missing files"""
        # Create document set with non-existent files
        doc_set = DocumentSet(
            set_id="missing_files",
            primary_document_id="doc1",
            documents={
                "doc1": DocumentMetadata(
                    file_path="/non/existent/file1.txt",
                    document_id="doc1",
                    source="test",
                    document_type="insurance"
                )
            },
            relationships=[]
        )
        
        with pytest.raises(FileNotFoundError):
            adapter.process_document_set(doc_set)
"""Integration tests for multi-document processing"""

import pytest
import os
from pathlib import Path
import json
import tempfile
import shutil
from unittest.mock import patch, Mock

from src.core.decision_tree_generator import DecisionTreeGenerator
from src.core.schemas import UnifiedDecisionTree
from src.utils.document_set_manager import DocumentSetManager
from src.adapters.multi_document_adapter import MultiDocumentAdapter


class TestMultiDocumentIntegration:
    """Integration tests for the complete multi-document processing flow"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files"""
        temp_path = tempfile.mkdtemp()
        yield Path(temp_path)
        shutil.rmtree(temp_path)
        
    @pytest.fixture
    def dupixent_example(self, temp_dir):
        """Create a realistic dupixent example"""
        # Insurance policy document
        insurance_file = temp_dir / "dupixent_insurance.txt"
        insurance_file.write_text("""
        DUPIXENT (dupilumab) Prior Authorization Criteria
        
        Covered for patients who meet ALL of the following:
        1. Age 12 years or older
        2. Diagnosis of moderate-to-severe atopic dermatitis
        3. Failed treatment with topical corticosteroids
        4. Prescribed by or in consultation with a dermatologist
        """)
        
        # Clinical guidelines document
        guidelines_file = temp_dir / "dupixent_guidelines.txt"
        guidelines_file.write_text("""
        Clinical Guidelines for DUPIXENT
        
        Additional criteria:
        - IGA score of 3 or greater
        - EASI score of 16 or greater
        - Body surface area involvement of 10% or greater
        - Consider step therapy with:
          * High-potency topical corticosteroids (4 weeks)
          * Topical calcineurin inhibitors if appropriate
        """)
        
        return {
            "insurance": insurance_file,
            "guidelines": guidelines_file
        }
        
    @pytest.fixture
    def manifest_example(self, temp_dir):
        """Create an example with a manifest file"""
        # Create documents
        primary_file = temp_dir / "humira_policy.txt"
        primary_file.write_text("Humira insurance policy content")
        
        supp_file = temp_dir / "humira_clinical.txt"
        supp_file.write_text("Humira clinical guidelines")
        
        # Create manifest
        manifest = {
            "set_id": "humira_complete_set",
            "primary_document_id": "humira_insurance",
            "documents": {
                "humira_insurance": {
                    "file_path": str(primary_file),
                    "document_id": "humira_insurance",
                    "source": "insurance_dept",
                    "document_type": "policy",
                    "effective_date": "2024-01-01"
                },
                "humira_clinical": {
                    "file_path": str(supp_file),
                    "document_id": "humira_clinical",
                    "source": "medical_dept",
                    "document_type": "guidelines",
                    "effective_date": "2024-01-01"
                }
            },
            "relationships": [
                {
                    "from_doc": "humira_insurance",
                    "to_doc": "humira_clinical",
                    "relationship_type": "cross_referenced",
                    "references": ["section_2.1", "appendix_A"]
                }
            ],
            "processing_metadata": {
                "version": "1.0",
                "created_by": "test_suite"
            }
        }
        
        manifest_file = temp_dir / "manifest.json"
        with open(manifest_file, 'w') as f:
            json.dump(manifest, f, indent=2)
            
        return {
            "primary": primary_file,
            "supplementary": supp_file,
            "manifest": manifest_file
        }
        
    @patch.dict(os.environ, {"ENABLE_MULTI_DOCUMENT": "true"})
    @patch('src.core.llm_client.LlmClient._call_api')
    def test_pattern_based_grouping_flow(self, mock_api_call, dupixent_example):
        """Test complete flow with pattern-based document grouping"""
        # Mock API responses
        mock_api_call.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": json.dumps({
                            "criteria": [
                                {"id": "c1", "type": "age", "condition": "12 years or older"}
                            ],
                            "tree": {"nodes": [{"id": "n1", "type": "decision"}]},
                            "valid": True,
                            "refined": {"final": "tree"}
                        })
                    }]
                }
            }]
        }
        
        # Initialize generator
        generator = DecisionTreeGenerator(verbose=True)
        
        # Process multiple documents
        result = generator.generate_from_documents([
            dupixent_example["insurance"],
            dupixent_example["guidelines"]
        ])
        
        # Verify result structure
        assert isinstance(result, UnifiedDecisionTree)
        assert len(result.source_documents) == 2
        assert result.metadata["merge_strategy"] == "simple_append"
        assert "supplementary_sections" in result.tree
        
    @patch.dict(os.environ, {"ENABLE_MULTI_DOCUMENT": "true"})
    @patch('src.core.llm_client.LlmClient._call_api')
    def test_manifest_based_flow(self, mock_api_call, manifest_example):
        """Test complete flow with manifest-based document grouping"""
        # Mock API responses
        mock_api_call.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": json.dumps({
                            "criteria": [{"id": "c1", "type": "diagnosis"}],
                            "tree": {"nodes": []},
                            "valid": True,
                            "refined": {"tree": "final"}
                        })
                    }]
                }
            }]
        }
        
        generator = DecisionTreeGenerator(verbose=False)
        
        # Process with manifest
        result = generator.generate_from_documents([
            manifest_example["primary"],
            manifest_example["supplementary"]
        ])
        
        assert isinstance(result, UnifiedDecisionTree)
        assert result.metadata["document_set_id"] == "humira_complete_set"
        assert len(result.metadata["relationships"]) == 1
        
    @patch.dict(os.environ, {"ENABLE_MULTI_DOCUMENT": "false"})
    @patch('src.core.llm_client.LlmClient._call_api')
    def test_multi_doc_disabled_behavior(self, mock_api_call, dupixent_example):
        """Test behavior when multi-document processing is disabled"""
        # Mock API response
        mock_api_call.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": json.dumps({
                            "criteria": [],
                            "tree": {"single": "doc"},
                            "valid": True,
                            "refined": {"single": "result"}
                        })
                    }]
                }
            }]
        }
        
        generator = DecisionTreeGenerator(verbose=True)
        
        # Try to process multiple documents
        result = generator.generate_from_documents([
            dupixent_example["insurance"],
            dupixent_example["guidelines"]
        ])
        
        # Should process only first document
        assert isinstance(result, dict)
        assert "single" in result
        assert result["single"] == "result"
        
    def test_document_set_manager_integration(self, dupixent_example):
        """Test DocumentSetManager integration"""
        manager = DocumentSetManager()
        
        # Test pattern-based identification
        doc_set = manager.identify_document_set([
            dupixent_example["insurance"],
            dupixent_example["guidelines"]
        ])
        
        assert doc_set is not None
        assert len(doc_set.documents) == 2
        assert doc_set.primary_document_id.startswith("dupixent_")
        assert len(doc_set.relationships) > 0
        
    @patch.dict(os.environ, {"ENABLE_MULTI_DOCUMENT": "true"})
    def test_error_handling_in_multi_doc_flow(self, temp_dir):
        """Test error handling in multi-document processing"""
        # Create files with one missing
        existing_file = temp_dir / "exists.txt"
        existing_file.write_text("content")
        
        missing_file = temp_dir / "missing.txt"
        
        with patch('src.core.llm_client.LlmClient._call_api'):
            generator = DecisionTreeGenerator()
            
            # Should handle missing file gracefully
            result = generator.generate_from_documents([existing_file, missing_file])
            
            # Should fall back to single document
            assert result is not None
            
    def test_end_to_end_manifest_creation(self, dupixent_example, temp_dir):
        """Test creating and using a manifest end-to-end"""
        manager = DocumentSetManager()
        
        # Identify document set
        doc_set = manager.identify_document_set([
            dupixent_example["insurance"],
            dupixent_example["guidelines"]
        ])
        
        # Save as manifest
        manifest_path = temp_dir / "test_manifest.json"
        manager.create_manifest(doc_set, manifest_path)
        
        assert manifest_path.exists()
        
        # Load and verify
        loaded_set = manager._load_from_manifest(manifest_path)
        
        assert loaded_set.set_id == doc_set.set_id
        assert len(loaded_set.documents) == len(doc_set.documents)
        assert len(loaded_set.relationships) == len(doc_set.relationships)
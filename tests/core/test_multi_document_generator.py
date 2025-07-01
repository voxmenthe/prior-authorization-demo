"""Tests for multi-document functionality in DecisionTreeGenerator"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import shutil
import os

from src.core.decision_tree_generator import DecisionTreeGenerator
from src.core.schemas import DocumentSet, DocumentMetadata, UnifiedDecisionTree
from src.core.config import AppConfig, Environment, ModelConfig


class TestMultiDocumentGenerator:
    """Test cases for multi-document functionality in DecisionTreeGenerator"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files"""
        temp_path = tempfile.mkdtemp()
        yield Path(temp_path)
        shutil.rmtree(temp_path)
        
    @pytest.fixture
    def mock_config_enabled(self):
        """Mock config with multi-document enabled"""
        config = Mock(spec=AppConfig)
        config.enable_multi_document = True
        config.multi_doc_merge_strategy = "simple_append"
        config.environment = Environment.TEST
        config.model_config = ModelConfig(
            primary_model="test-model",
            fallback_model="test-fallback",
            description="Test config"
        )
        config.api_key = "test-key"
        return config
        
    @pytest.fixture
    def mock_config_disabled(self):
        """Mock config with multi-document disabled"""
        config = Mock(spec=AppConfig)
        config.enable_multi_document = False
        config.environment = Environment.TEST
        config.model_config = ModelConfig(
            primary_model="test-model",
            fallback_model="test-fallback",
            description="Test config"
        )
        config.api_key = "test-key"
        return config
        
    @pytest.fixture
    def sample_files(self, temp_dir):
        """Create sample test files"""
        files = {
            "insurance": temp_dir / "drug_insurance.txt",
            "guidelines": temp_dir / "drug_guidelines.txt",
            "single": temp_dir / "single_doc.txt"
        }
        
        files["insurance"].write_text("Insurance criteria content")
        files["guidelines"].write_text("Clinical guidelines content")
        files["single"].write_text("Single document content")
        
        return files
        
    @patch('src.core.decision_tree_generator.get_config')
    @patch('src.core.decision_tree_generator.LlmClient')
    def test_single_document_processing(self, mock_llm, mock_get_config, mock_config_disabled, sample_files):
        """Test that single document processing works as before"""
        mock_get_config.return_value = mock_config_disabled
        
        generator = DecisionTreeGenerator(verbose=False)
        
        # Mock the agents to return simple results
        generator.parser_agent.parse = Mock(return_value={"criteria": []})
        generator.structure_agent.create_tree = Mock(return_value={"tree": "structure"})
        generator.validation_agent.validate = Mock(return_value={"valid": True})
        generator.refinement_agent.refine = Mock(return_value={"final": "tree"})
        
        # Test single document path
        result = generator.generate_from_documents(sample_files["single"])
        
        assert isinstance(result, dict)
        assert result == {"final": "tree"}
        
    @patch('src.core.decision_tree_generator.get_config')
    @patch('src.core.decision_tree_generator.LlmClient')
    def test_multi_document_enabled_processing(self, mock_llm, mock_get_config, mock_config_enabled, sample_files):
        """Test multi-document processing when enabled"""
        mock_get_config.return_value = mock_config_enabled
        
        generator = DecisionTreeGenerator(verbose=True)
        
        # Mock the agents
        generator.parser_agent.parse = Mock(return_value={"criteria": []})
        generator.structure_agent.create_tree = Mock(return_value={"tree": "structure"})
        generator.validation_agent.validate = Mock(return_value={"valid": True})
        generator.refinement_agent.refine = Mock(return_value={"final": "tree"})
        
        # Test with multiple documents
        with patch.object(generator.document_set_manager, 'identify_document_set') as mock_identify:
            mock_doc_set = DocumentSet(
                set_id="test_set",
                primary_document_id="doc1",
                documents={
                    "doc1": DocumentMetadata(
                        file_path=str(sample_files["insurance"]),
                        document_id="doc1",
                        source="test",
                        document_type="insurance"
                    ),
                    "doc2": DocumentMetadata(
                        file_path=str(sample_files["guidelines"]),
                        document_id="doc2",
                        source="test",
                        document_type="guidelines"
                    )
                },
                relationships=[]
            )
            mock_identify.return_value = mock_doc_set
            
            result = generator.generate_from_documents([
                sample_files["insurance"],
                sample_files["guidelines"]
            ])
            
            assert isinstance(result, UnifiedDecisionTree)
            assert len(result.source_documents) == 2
            
    @patch('src.core.decision_tree_generator.get_config')
    @patch('src.core.decision_tree_generator.LlmClient')
    def test_multi_document_disabled_with_multiple_files(self, mock_llm, mock_get_config, mock_config_disabled, sample_files):
        """Test that multiple files only process first when multi-doc is disabled"""
        mock_get_config.return_value = mock_config_disabled
        
        generator = DecisionTreeGenerator(verbose=True)
        
        # Mock the agents
        generator.parser_agent.parse = Mock(return_value={"criteria": []})
        generator.structure_agent.create_tree = Mock(return_value={"tree": "structure"})
        generator.validation_agent.validate = Mock(return_value={"valid": True})
        generator.refinement_agent.refine = Mock(return_value={"first": "doc"})
        
        # Test with multiple documents
        result = generator.generate_from_documents([
            sample_files["insurance"],
            sample_files["guidelines"]
        ])
        
        # Should only process first document
        assert isinstance(result, dict)
        assert result == {"first": "doc"}
        
    @patch('src.core.decision_tree_generator.get_config')
    @patch('src.core.decision_tree_generator.LlmClient')
    def test_process_document_set_with_disabled_multi_doc(self, mock_llm, mock_get_config, mock_config_disabled):
        """Test that process_document_set raises error when multi-doc is disabled"""
        mock_get_config.return_value = mock_config_disabled
        
        generator = DecisionTreeGenerator()
        
        mock_doc_set = Mock(spec=DocumentSet)
        
        with pytest.raises(ValueError, match="Multi-document processing is not enabled"):
            generator.process_document_set(mock_doc_set)
            
    @patch('src.core.decision_tree_generator.get_config')
    @patch('src.core.decision_tree_generator.LlmClient')
    def test_fallback_to_single_when_no_relationships(self, mock_llm, mock_get_config, mock_config_enabled, sample_files):
        """Test fallback to single document when relationships can't be identified"""
        mock_get_config.return_value = mock_config_enabled
        
        generator = DecisionTreeGenerator(verbose=True)
        
        # Mock the agents
        generator.parser_agent.parse = Mock(return_value={"criteria": []})
        generator.structure_agent.create_tree = Mock(return_value={"tree": "structure"})
        generator.validation_agent.validate = Mock(return_value={"valid": True})
        generator.refinement_agent.refine = Mock(return_value={"fallback": "result"})
        
        # Mock document set manager to return None
        with patch.object(generator.document_set_manager, 'identify_document_set', return_value=None):
            result = generator.generate_from_documents([
                sample_files["insurance"],
                sample_files["guidelines"]
            ])
            
            # Should fall back to single document processing
            assert isinstance(result, dict)
            assert result == {"fallback": "result"}
            
    @patch('src.core.decision_tree_generator.get_config')
    @patch('src.core.decision_tree_generator.LlmClient')
    def test_lazy_adapter_initialization(self, mock_llm, mock_get_config, mock_config_enabled):
        """Test that multi-doc adapter is lazily initialized"""
        mock_get_config.return_value = mock_config_enabled
        
        generator = DecisionTreeGenerator()
        
        # Adapter should not be initialized yet
        assert generator.multi_doc_adapter is None
        
        # Create a mock document set
        mock_doc_set = Mock(spec=DocumentSet)
        mock_doc_set.documents = {}
        mock_doc_set.primary_document_id = "test"
        
        # Process document set should initialize adapter
        with patch('src.adapters.multi_document_adapter.MultiDocumentAdapter') as mock_adapter_class:
            mock_adapter = Mock()
            mock_adapter.process_document_set.return_value = Mock(spec=UnifiedDecisionTree)
            mock_adapter_class.return_value = mock_adapter
            
            generator.process_document_set(mock_doc_set)
            
            # Adapter should now be initialized
            assert generator.multi_doc_adapter is not None
            mock_adapter_class.assert_called_once_with(generator)
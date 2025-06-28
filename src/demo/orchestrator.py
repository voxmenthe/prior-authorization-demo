"""
Demo Orchestrator - Main controller for demo execution.

This module coordinates the processing of multiple documents through the
Prior Authorization Decision Tree Generation pipeline with comprehensive
error handling and performance tracking.
"""

import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from src.core.decision_tree_generator import DecisionTreeGenerator
from src.utils.json_utils import normalize_json_output
from src.core.exceptions import (
    DecisionTreeGenerationError,
    CriteriaParsingError,
    TreeStructureError,
    ValidationError,
    RefinementError
)


@dataclass
class DocumentResult:
    """Result of processing a single document."""
    document_name: str
    success: bool
    processing_time: float
    decision_tree: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    api_calls: int = 0
    tokens_used: int = 0
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class DemoSession:
    """Represents a complete demo session."""
    started_at: datetime
    completed_at: Optional[datetime] = None
    mode: str = "interactive"
    total_documents: int = 0
    successful_documents: int = 0
    failed_documents: int = 0
    total_processing_time: float = 0.0
    total_api_calls: int = 0
    total_tokens: int = 0
    document_results: List[DocumentResult] = None

    def __post_init__(self):
        if self.document_results is None:
            self.document_results = []


class DemoOrchestrator:
    """
    Main controller for demo execution.
    
    Coordinates the processing of multiple documents through the pipeline,
    handles errors gracefully, and collects comprehensive metrics.
    """

    def __init__(self, output_dir: str = "outputs", verbose: bool = False):
        """
        Initialize the demo orchestrator.
        
        Args:
            output_dir: Directory for saving output files
            verbose: Enable verbose logging
        """
        self.output_dir = Path(output_dir)
        self.verbose = verbose
        self.generator = DecisionTreeGenerator(verbose=verbose)
        self.session: Optional[DemoSession] = None
        
        # Create output directories
        self.output_dir.mkdir(exist_ok=True)
        (self.output_dir / "decision_trees").mkdir(exist_ok=True)
        (self.output_dir / "reports").mkdir(exist_ok=True)
        (self.output_dir / "logs").mkdir(exist_ok=True)

    def start_session(self, mode: str = "interactive") -> DemoSession:
        """Start a new demo session."""
        self.session = DemoSession(
            started_at=datetime.now(),
            mode=mode
        )
        return self.session

    def process_document(self, document_path: str, document_name: str = None) -> DocumentResult:
        """
        Process a single document through the pipeline.
        
        Args:
            document_path: Path to the criteria document
            document_name: Optional display name for the document
            
        Returns:
            DocumentResult with processing outcomes and metrics
        """
        if document_name is None:
            document_name = Path(document_path).name

        start_time = time.time()
        
        try:
            # Load document content
            with open(document_path, 'r', encoding='utf-8') as f:
                document_content = f.read()
            
            # Process through pipeline
            decision_tree = self.generator.generate_decision_tree(document_content)
            
            processing_time = time.time() - start_time
            
            # Create successful result
            result = DocumentResult(
                document_name=document_name,
                success=True,
                processing_time=processing_time,
                decision_tree=decision_tree,
                metadata={
                    "document_path": str(document_path),
                    "document_size": len(document_content),
                    "generated_at": datetime.now().isoformat()
                }
            )
            
            # Save decision tree to file
            self._save_decision_tree(result)
            
            # Add to session if one exists
            if self.session:
                self.session.document_results.append(result)
                self.session.total_documents += 1
                if result.success:
                    self.session.successful_documents += 1
            
            return result
            
        except FileNotFoundError as e:
            processing_time = time.time() - start_time
            result = DocumentResult(
                document_name=document_name,
                success=False,
                processing_time=processing_time,
                error=f"File not found: {str(e)}"
            )
            
            # Add to session if one exists
            if self.session:
                self.session.document_results.append(result)
                self.session.total_documents += 1
            
            return result
            
        except (CriteriaParsingError, TreeStructureError, ValidationError, RefinementError) as e:
            processing_time = time.time() - start_time
            result = DocumentResult(
                document_name=document_name,
                success=False,
                processing_time=processing_time,
                error=f"Pipeline error: {str(e)}"
            )
            
            # Add to session if one exists
            if self.session:
                self.session.document_results.append(result)
                self.session.total_documents += 1
            
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            result = DocumentResult(
                document_name=document_name,
                success=False,
                processing_time=processing_time,
                error=f"Unexpected error: {str(e)}"
            )
            
            # Add to session if one exists
            if self.session:
                self.session.document_results.append(result)
                self.session.total_documents += 1
            
            return result

    def process_multiple_documents(self, document_paths: List[str]) -> List[DocumentResult]:
        """
        Process multiple documents through the pipeline.
        
        Args:
            document_paths: List of paths to criteria documents
            
        Returns:
            List of DocumentResult objects
        """
        if not self.session:
            self.start_session()
            
        self.session.total_documents = len(document_paths)
        results = []
        
        for doc_path in document_paths:
            result = self.process_document(doc_path)
            results.append(result)
            self.session.document_results.append(result)
            
            # Update session metrics
            if result.success:
                self.session.successful_documents += 1
            else:
                self.session.failed_documents += 1
                
            self.session.total_processing_time += result.processing_time
            self.session.total_api_calls += result.api_calls
            self.session.total_tokens += result.tokens_used
        
        return results

    def complete_session(self) -> DemoSession:
        """Complete the current demo session and generate final report."""
        if not self.session:
            raise ValueError("No active session to complete")
            
        self.session.completed_at = datetime.now()
        
        # Generate session report
        self._save_session_report()
        
        return self.session

    def get_example_documents(self) -> List[str]:
        """Get list of available example documents."""
        examples_dir = Path("examples")
        if not examples_dir.exists():
            return []
            
        return [
            str(examples_dir / "ozempic_criteria.txt"),
            str(examples_dir / "jardiance_criteria.txt"),
            str(examples_dir / "cardioguard_criteria.txt")
        ]

    def _save_decision_tree(self, result: DocumentResult) -> None:
        """Save decision tree result to JSON file."""
        if not result.success or not result.decision_tree:
            return
            
        filename = f"{result.document_name.replace('.txt', '')}_decision_tree.json"
        filepath = self.output_dir / "decision_trees" / filename
        
        output_data = {
            "metadata": {
                "document": result.document_name,
                "generated_at": datetime.now().isoformat(),
                "pipeline_version": "1.0.0",
                "processing_time_seconds": result.processing_time,
                "api_calls": result.api_calls,
                "tokens_used": result.tokens_used
            },
            "decision_tree": result.decision_tree,
            "processing_metrics": {
                "success": result.success,
                "processing_time": result.processing_time
            }
        }
        
        if result.metadata:
            output_data["metadata"].update(result.metadata)
        
        # Normalize the JSON output before saving
        normalized_data = normalize_json_output(output_data)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            # Write the normalized JSON string directly
            f.write(normalized_data)

    def _save_session_report(self) -> None:
        """Save comprehensive session report."""
        if not self.session:
            return
            
        timestamp = self.session.started_at.strftime("%Y%m%d_%H%M%S")
        filename = f"demo_session_{timestamp}.json"
        filepath = self.output_dir / "reports" / filename
        
        # Calculate session duration
        duration = None
        if self.session.completed_at:
            duration = (self.session.completed_at - self.session.started_at).total_seconds()
        
        report_data = {
            "demo_session": {
                "started_at": self.session.started_at.isoformat(),
                "completed_at": self.session.completed_at.isoformat() if self.session.completed_at else None,
                "total_duration_seconds": duration,
                "mode": self.session.mode
            },
            "summary": {
                "total_documents": self.session.total_documents,
                "successful_documents": self.session.successful_documents,
                "failed_documents": self.session.failed_documents,
                "success_rate": self.session.successful_documents / max(1, self.session.total_documents),
                "total_processing_time": self.session.total_processing_time,
                "average_processing_time": self.session.total_processing_time / max(1, self.session.total_documents),
                "total_api_calls": self.session.total_api_calls,
                "total_tokens": self.session.total_tokens
            },
            "document_results": [
                {
                    "document_name": result.document_name,
                    "success": result.success,
                    "processing_time": result.processing_time,
                    "error": result.error,
                    "api_calls": result.api_calls,
                    "tokens_used": result.tokens_used,
                    "has_decision_tree": result.decision_tree is not None
                }
                for result in self.session.document_results
            ]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

    def get_session_summary(self) -> Dict[str, Any]:
        """Get current session summary for display."""
        if not self.session:
            return {}
            
        return {
            "total_documents": self.session.total_documents,
            "successful": self.session.successful_documents,
            "failed": self.session.failed_documents,
            "total_time": self.session.total_processing_time,
            "avg_time": self.session.total_processing_time / max(1, len(self.session.document_results)),
            "api_calls": self.session.total_api_calls,
            "tokens": self.session.total_tokens
        }
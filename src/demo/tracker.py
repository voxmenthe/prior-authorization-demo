"""
Progress Tracker - Performance monitoring and metrics collection.

This module tracks processing time, API usage, token consumption, and other
performance metrics throughout the demo execution.
"""

import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from contextlib import contextmanager


@dataclass
class StepMetrics:
    """Metrics for a single processing step."""
    step_name: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration: Optional[float] = None
    success: bool = False
    error: Optional[str] = None
    api_calls: int = 0
    tokens_used: int = 0
    memory_usage: Optional[float] = None
    custom_metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DocumentMetrics:
    """Comprehensive metrics for processing a single document."""
    document_name: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    total_duration: Optional[float] = None
    success: bool = False
    error: Optional[str] = None
    steps: List[StepMetrics] = field(default_factory=list)
    
    @property
    def total_api_calls(self) -> int:
        """Total API calls across all steps."""
        return sum(step.api_calls for step in self.steps)
    
    @property
    def total_tokens(self) -> int:
        """Total tokens used across all steps."""
        return sum(step.tokens_used for step in self.steps)
    
    @property
    def step_durations(self) -> Dict[str, float]:
        """Duration of each step."""
        return {
            step.step_name: step.duration or 0.0 
            for step in self.steps 
            if step.duration is not None
        }


class ProgressTracker:
    """
    Performance monitoring and metrics collection.
    
    Tracks detailed metrics for each document processing session,
    including step-by-step timing, API usage, and error tracking.
    """
    
    def __init__(self):
        """Initialize the progress tracker."""
        self.current_document: Optional[DocumentMetrics] = None
        self.current_step: Optional[StepMetrics] = None
        self.document_history: List[DocumentMetrics] = []
        self.session_started_at: Optional[datetime] = None
        
    def start_session(self) -> None:
        """Start tracking a new demo session."""
        self.session_started_at = datetime.now()
        self.document_history.clear()
        
    def start_document(self, document_name: str) -> DocumentMetrics:
        """
        Start tracking metrics for a new document.
        
        Args:
            document_name: Name of the document being processed
            
        Returns:
            DocumentMetrics object for the new document
        """
        # Finish previous document if exists
        if self.current_document and not self.current_document.completed_at:
            self.finish_document(success=False, error="Interrupted by new document")
        
        self.current_document = DocumentMetrics(
            document_name=document_name,
            started_at=datetime.now()
        )
        
        return self.current_document
    
    def finish_document(self, success: bool, error: str = None) -> DocumentMetrics:
        """
        Finish tracking the current document.
        
        Args:
            success: Whether document processing succeeded
            error: Error message if processing failed
            
        Returns:
            Completed DocumentMetrics object
        """
        if not self.current_document:
            raise ValueError("No active document to finish")
        
        # Finish current step if exists
        if self.current_step and not self.current_step.completed_at:
            self.finish_step(success=success, error=error)
        
        self.current_document.completed_at = datetime.now()
        self.current_document.total_duration = (
            self.current_document.completed_at - self.current_document.started_at
        ).total_seconds()
        self.current_document.success = success
        self.current_document.error = error
        
        # Add to history
        self.document_history.append(self.current_document)
        completed_doc = self.current_document
        self.current_document = None
        
        return completed_doc
    
    @contextmanager
    def track_step(self, step_name: str):
        """
        Context manager for tracking a processing step.
        
        Args:
            step_name: Name of the processing step
            
        Usage:
            with tracker.track_step("Criteria Parsing"):
                # Process criteria
                pass
        """
        step_metrics = self.start_step(step_name)
        try:
            yield step_metrics
            self.finish_step(success=True)
        except Exception as e:
            self.finish_step(success=False, error=str(e))
            raise
    
    def start_step(self, step_name: str) -> StepMetrics:
        """
        Start tracking a new processing step.
        
        Args:
            step_name: Name of the processing step
            
        Returns:
            StepMetrics object for the new step
        """
        if not self.current_document:
            raise ValueError("No active document for step tracking")
        
        # Finish previous step if exists
        if self.current_step and not self.current_step.completed_at:
            self.finish_step(success=True)
        
        self.current_step = StepMetrics(
            step_name=step_name,
            started_at=datetime.now()
        )
        
        return self.current_step
    
    def finish_step(self, success: bool, error: str = None) -> StepMetrics:
        """
        Finish tracking the current step.
        
        Args:
            success: Whether step processing succeeded
            error: Error message if step failed
            
        Returns:
            Completed StepMetrics object
        """
        if not self.current_step:
            raise ValueError("No active step to finish")
        
        if not self.current_document:
            raise ValueError("No active document for step")
        
        self.current_step.completed_at = datetime.now()
        self.current_step.duration = (
            self.current_step.completed_at - self.current_step.started_at
        ).total_seconds()
        self.current_step.success = success
        self.current_step.error = error
        
        # Add to document steps
        self.current_document.steps.append(self.current_step)
        completed_step = self.current_step
        self.current_step = None
        
        return completed_step
    
    def add_api_call(self, tokens_used: int = 0) -> None:
        """
        Record an API call for the current step.
        
        Args:
            tokens_used: Number of tokens consumed by the API call
        """
        if self.current_step:
            self.current_step.api_calls += 1
            self.current_step.tokens_used += tokens_used
    
    def add_custom_metric(self, key: str, value: Any) -> None:
        """
        Add a custom metric to the current step.
        
        Args:
            key: Metric name
            value: Metric value
        """
        if self.current_step:
            self.current_step.custom_metrics[key] = value
    
    def get_session_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive session summary.
        
        Returns:
            Dictionary with session metrics and statistics
        """
        if not self.session_started_at:
            return {}
        
        now = datetime.now()
        session_duration = (now - self.session_started_at).total_seconds()
        
        # Calculate aggregates
        total_documents = len(self.document_history)
        successful_documents = sum(1 for doc in self.document_history if doc.success)
        failed_documents = total_documents - successful_documents
        
        total_processing_time = sum(
            doc.total_duration for doc in self.document_history 
            if doc.total_duration is not None
        )
        
        total_api_calls = sum(doc.total_api_calls for doc in self.document_history)
        total_tokens = sum(doc.total_tokens for doc in self.document_history)
        
        # Performance metrics
        avg_processing_time = total_processing_time / max(1, total_documents)
        success_rate = successful_documents / max(1, total_documents)
        
        return {
            "session": {
                "started_at": self.session_started_at.isoformat(),
                "duration": session_duration,
                "status": "active" if self.current_document else "completed"
            },
            "documents": {
                "total": total_documents,
                "successful": successful_documents,
                "failed": failed_documents,
                "success_rate": success_rate
            },
            "performance": {
                "total_processing_time": total_processing_time,
                "average_processing_time": avg_processing_time,
                "total_api_calls": total_api_calls,
                "total_tokens": total_tokens,
                "tokens_per_document": total_tokens / max(1, total_documents),
                "api_calls_per_document": total_api_calls / max(1, total_documents)
            },
            "step_performance": self._get_step_performance_summary()
        }
    
    def get_document_summary(self, document_name: str) -> Optional[Dict[str, Any]]:
        """
        Get summary for a specific document.
        
        Args:
            document_name: Name of the document
            
        Returns:
            Dictionary with document metrics or None if not found
        """
        for doc in self.document_history:
            if doc.document_name == document_name:
                return {
                    "document_name": doc.document_name,
                    "success": doc.success,
                    "total_duration": doc.total_duration,
                    "error": doc.error,
                    "steps": len(doc.steps),
                    "api_calls": doc.total_api_calls,
                    "tokens": doc.total_tokens,
                    "step_durations": doc.step_durations
                }
        return None
    
    def _get_step_performance_summary(self) -> Dict[str, Dict[str, float]]:
        """Get performance summary by step type."""
        step_stats = {}
        
        for doc in self.document_history:
            for step in doc.steps:
                step_name = step.step_name
                if step_name not in step_stats:
                    step_stats[step_name] = {
                        "total_duration": 0.0,
                        "count": 0,
                        "successes": 0,
                        "failures": 0,
                        "total_api_calls": 0,
                        "total_tokens": 0
                    }
                
                stats = step_stats[step_name]
                stats["count"] += 1
                
                if step.duration:
                    stats["total_duration"] += step.duration
                
                if step.success:
                    stats["successes"] += 1
                else:
                    stats["failures"] += 1
                
                stats["total_api_calls"] += step.api_calls
                stats["total_tokens"] += step.tokens_used
        
        # Calculate averages
        for step_name, stats in step_stats.items():
            if stats["count"] > 0:
                stats["average_duration"] = stats["total_duration"] / stats["count"]
                stats["success_rate"] = stats["successes"] / stats["count"]
                stats["avg_api_calls"] = stats["total_api_calls"] / stats["count"]
                stats["avg_tokens"] = stats["total_tokens"] / stats["count"]
        
        return step_stats
    
    def export_metrics(self) -> Dict[str, Any]:
        """
        Export all collected metrics for external analysis.
        
        Returns:
            Complete metrics data structure
        """
        return {
            "session_summary": self.get_session_summary(),
            "document_history": [
                {
                    "document_name": doc.document_name,
                    "started_at": doc.started_at.isoformat(),
                    "completed_at": doc.completed_at.isoformat() if doc.completed_at else None,
                    "total_duration": doc.total_duration,
                    "success": doc.success,
                    "error": doc.error,
                    "total_api_calls": doc.total_api_calls,
                    "total_tokens": doc.total_tokens,
                    "steps": [
                        {
                            "step_name": step.step_name,
                            "started_at": step.started_at.isoformat(),
                            "completed_at": step.completed_at.isoformat() if step.completed_at else None,
                            "duration": step.duration,
                            "success": step.success,
                            "error": step.error,
                            "api_calls": step.api_calls,
                            "tokens_used": step.tokens_used,
                            "custom_metrics": step.custom_metrics
                        }
                        for step in doc.steps
                    ]
                }
                for doc in self.document_history
            ]
        }
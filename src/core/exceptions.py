"""Custom exceptions for the decision tree generation system."""

from enum import Enum


class ConflictType(Enum):
    """Types of conflicts that can occur in decision trees."""
    CONTRADICTORY_PATHS = "contradictory_paths"
    CIRCULAR_DEPENDENCY = "circular_dependency"
    REDUNDANT_PATHS = "redundant_paths"
    OVERLAPPING_CONDITIONS = "overlapping_conditions"
    INCOMPLETE_COVERAGE = "incomplete_coverage"


class DecisionTreeGenerationError(Exception):
    """Base exception for decision tree generation errors."""
    pass


class CriteriaParsingError(DecisionTreeGenerationError):
    """Exception raised when criteria parsing fails."""
    pass


class TreeStructureError(DecisionTreeGenerationError):
    """Exception raised when tree structure creation fails."""
    pass


class ValidationError(DecisionTreeGenerationError):
    """Exception raised when tree validation fails."""
    pass


class RefinementError(DecisionTreeGenerationError):
    """Exception raised when tree refinement fails."""
    pass
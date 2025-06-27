"""Custom exceptions for the decision tree generation system."""


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
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum

# Generic KeyValuePair for Gemini API compatibility
class KeyValuePair(BaseModel):
    key: str
    value: str

    @classmethod
    def from_dict(cls, data: dict) -> List['KeyValuePair']:
        """Convert dictionary to list of KeyValuePairs."""
        return [cls(key=str(k), value=str(v)) for k, v in data.items()]
    
    @classmethod
    def to_dict(cls, pairs: List['KeyValuePair']) -> dict:
        """Convert list of KeyValuePairs to dictionary."""
        return {pair.key: pair.value for pair in pairs}

# For criteria_parser_agent.py
class CriterionParameter(BaseModel):
    threshold_value: Optional[str] = None
    threshold_operator: Optional[str] = None
    unit: Optional[str] = None

class Criterion(BaseModel):
    id: str
    type: str
    condition: str
    parameters: CriterionParameter
    sub_conditions: List[Any] = Field(default_factory=list)
    exceptions: List[Any] = Field(default_factory=list)

class ParsedCriteria(BaseModel):
    criteria: List[Criterion]

# For tree_structure_agent.py
class QuestionOrder(BaseModel):
    ordered_ids: List[str]
    reasoning: str

class NodeConnection(BaseModel):
    target_node_id: str
    condition: str
    condition_value: Optional[str] = None

class DecisionNode(BaseModel):
    id: str
    type: str
    question: str
    data_type: str
    help_text: Optional[str] = None
    validation: List[KeyValuePair] = Field(default_factory=list)
    connections: List[NodeConnection] = Field(default_factory=list)

# For validation_agent.py
class ValidationIssue(BaseModel):
    node_id: str
    explanation: str

class LogicalConsistencyCheck(BaseModel):
    issues: List[ValidationIssue]

class CompletenessIssue(BaseModel):
    """An issue related to the completeness of the decision tree."""
    issue_type: str = Field(description="Type of completeness issue (e.g., 'missing_criteria', 'incomplete_pathway', 'unaddressed_edge_case')")
    description: str = Field(description="Detailed description of the issue.")
    missing_criteria: Optional[List[str]] = Field(default=None, description="List of specific criteria that are missing.")
    affected_nodes: Optional[List[str]] = Field(default=None, description="Node IDs related to the issue.")
    
    def to_validation_issue(self) -> ValidationIssue:
        """Convert to ValidationIssue format for consistency."""
        node_id = self.affected_nodes[0] if self.affected_nodes else "unknown"
        return ValidationIssue(node_id=node_id, explanation=self.description)

class CompletenessCheck(BaseModel):
    """The result of a completeness check."""
    issues: List[CompletenessIssue]

class AmbiguityIssue(BaseModel):
    """An issue related to ambiguity in the decision tree."""
    node_id: str = Field(description="The ID of the node with ambiguous language.")
    ambiguous_text: str = Field(description="The specific text that is ambiguous.")
    issue_type: str = Field(description="Type of ambiguity (e.g., 'vague_condition', 'missing_threshold', 'unclear_terminology')")
    suggestion: str = Field(description="A suggestion for how to resolve the ambiguity.")
    
    def to_validation_issue(self) -> ValidationIssue:
        """Convert to ValidationIssue format for consistency."""
        return ValidationIssue(
            node_id=self.node_id, 
            explanation=f"{self.issue_type}: {self.ambiguous_text} - {self.suggestion}"
        )

class AmbiguityCheck(BaseModel):
    """The result of an ambiguity check."""
    issues: List[AmbiguityIssue]

# For refinement_agent.py
class RefinedTreeSection(BaseModel):
    # This schema will depend heavily on the tree structure itself.
    # For now, we represent it as a list of key-value pairs for Gemini compatibility.
    corrected_section: List[KeyValuePair]

# For conflict_resolver.py
class NodeModification(BaseModel):
    """A modification to apply to a node."""
    node_id: str
    modification_type: str = Field(description="Type of modification: 'update_condition', 'add_connection', 'remove_connection', 'update_text'")
    old_value: Optional[str] = None
    new_value: str
    
class ConflictResolution(BaseModel):
    """Resolution for a specific conflict."""
    conflict_type: str
    description: str
    modified_nodes: List[NodeModification]
    new_nodes: Optional[List[DecisionNode]] = None
    removed_connections: Optional[List[str]] = None
    confidence_score: float = Field(ge=0.0, le=1.0)
    reasoning: str

# Multi-document support schemas
class DocumentRelationType(str, Enum):
    PRIMARY_SUPPLEMENTARY = "primary_supplementary"
    PEER = "peer"
    TEMPORAL_UPDATE = "temporal_update"
    CROSS_REFERENCED = "cross_referenced"

class DocumentMetadata(BaseModel):
    """Metadata for a document in a set"""
    file_path: str
    document_id: str
    source: str
    document_type: str
    effective_date: Optional[str] = None
    
class DocumentRelationship(BaseModel):
    """Represents a relationship between two documents"""
    from_doc: str
    to_doc: str
    relationship_type: DocumentRelationType
    references: List[str] = Field(default_factory=list)  # Specific sections referenced

class DocumentSet(BaseModel):
    """Represents a set of related documents"""
    set_id: str
    primary_document_id: str
    documents: Dict[str, DocumentMetadata]
    relationships: List[DocumentRelationship]
    processing_metadata: Dict[str, Any] = Field(default_factory=dict)

class UnifiedDecisionTree(BaseModel):
    """Result of multi-document processing"""
    tree: Dict[str, Any]  # The actual decision tree
    source_documents: List[str]  # Document IDs that contributed
    metadata: Dict[str, Any]
    extracted_references: List[Dict] = Field(default_factory=list)  # For future use
    resolved_references_count: int = 0  # For future use

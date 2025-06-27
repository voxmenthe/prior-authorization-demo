from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

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

# For refinement_agent.py
class RefinedTreeSection(BaseModel):
    # This schema will depend heavily on the tree structure itself.
    # For now, we represent it as a list of key-value pairs for Gemini compatibility.
    corrected_section: List[KeyValuePair]

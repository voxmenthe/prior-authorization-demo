# Core Authorization Pipeline API Documentation

## Overview

The Prior Authorization Demo system implements a sophisticated pipeline for transforming medical criteria documents into executable decision trees. This document covers the core authorization components and their APIs.

## Core Components

### 1. DecisionTreeGenerator

**Location**: `src/core/decision_tree_generator.py:6-45`

The central orchestrator that manages the entire pipeline flow.

```python
class DecisionTreeGenerator:
    def __init__(self, llm_client: LlmClient, verbose: bool = False)
```

#### Methods

##### `generate_decision_tree(ocr_text: str) -> dict`
**Location**: `src/core/decision_tree_generator.py:18-45`

Orchestrates the complete pipeline to generate a decision tree from OCR text.

**Parameters:**
- `ocr_text` (str): Raw text extracted from medical criteria documents

**Returns:**
- `dict`: Complete decision tree with nodes, connections, and metadata

**Pipeline Steps:**
1. Parse criteria using `CriteriaParserAgent`
2. Create tree structure using `TreeStructureAgent`
3. Validate tree using `ValidationAgent`
4. Refine tree using `RefinementAgent`

**Raises:**
- `DecisionTreeGenerationError`: Base exception for pipeline failures
- `CriteriaParsingError`: When criteria extraction fails
- `TreeStructureError`: When tree creation fails
- `ValidationError`: When validation identifies critical issues
- `RefinementError`: When refinement process fails

**Example:**
```python
generator = DecisionTreeGenerator(llm_client, verbose=True)
tree = generator.generate_decision_tree(ocr_text)
```

### 2. LlmClient

**Location**: `src/core/llm_client.py:39-221`

Manages LLM interactions with fallback support and structured output generation.

```python
class LlmClient:
    def __init__(self, 
                 model_name: Optional[str] = None,
                 fallback_model_name: Optional[str] = None,
                 verbose: bool = False)
```

#### Key Methods

##### `generate_text(prompt: str, system_instruction: Optional[str] = None) -> str`
**Location**: `src/core/llm_client.py:139-154`

Generates free-form text responses.

**Parameters:**
- `prompt` (str): User prompt
- `system_instruction` (Optional[str]): System-level instructions

**Returns:**
- `str`: Generated text response

##### `generate_structured_json(prompt: str, schema: Type[T], system_instruction: Optional[str] = None) -> T`
**Location**: `src/core/llm_client.py:156-182`

Generates structured JSON conforming to a Pydantic schema.

**Parameters:**
- `prompt` (str): User prompt
- `schema` (Type[T]): Pydantic model class for response structure
- `system_instruction` (Optional[str]): System-level instructions

**Returns:**
- `T`: Instance of the provided Pydantic model

**Features:**
- Automatic retry with fallback model
- JSON mode fallback for non-conforming responses
- Schema conversion for Gemini API compatibility

### 3. Data Schemas

**Location**: `src/core/schemas.py:4-66`

#### Core Schema Classes

##### `Criterion`
**Location**: `src/core/schemas.py:24-30`

Represents a single medical criterion.

```python
class Criterion:
    type: str  # "INCLUSIONARY", "EXCLUSIONARY", "DOCUMENTATION"
    description: str
    conditions: List[str]
    thresholds: Optional[Dict[str, Any]]
    exceptions: Optional[List[str]]
    logical_operator: Optional[str]  # "AND", "OR"
```

##### `DecisionNode`
**Location**: `src/core/schemas.py:45-52`

Represents a node in the decision tree.

```python
class DecisionNode:
    id: str
    type: str  # "question", "outcome"
    content: str
    question: Optional[str]
    options: Optional[List[str]]
    outcome: Optional[str]  # "APPROVED", "DENIED"
    reason: Optional[str]
```

##### `NodeConnection`
**Location**: `src/core/schemas.py:40-43`

Defines connections between nodes.

```python
class NodeConnection:
    from_node: str
    to_node: str
    condition: str
```

##### `ValidationIssue`
**Location**: `src/core/schemas.py:55-57`

Represents issues found during validation.

```python
class ValidationIssue:
    severity: str  # "ERROR", "WARNING"
    message: str
```

## Agent APIs

### 1. CriteriaParserAgent

**Location**: `src/agents/criteria_parser_agent.py:5-76`

Extracts structured criteria from raw text.

#### Methods

##### `parse(ocr_text: str) -> dict`
**Location**: `src/agents/criteria_parser_agent.py:12-37`

**Parameters:**
- `ocr_text` (str): Raw OCR text

**Returns:**
```python
{
    "indications": List[str],
    "criteria": {
        "INCLUSIONARY": List[Criterion],
        "EXCLUSIONARY": List[Criterion],
        "DOCUMENTATION": List[Criterion]
    }
}
```

### 2. TreeStructureAgent

**Location**: `src/agents/tree_structure_agent.py:6-370`

Creates decision tree structure from parsed criteria.

#### Methods

##### `create_tree(parsed_criteria: dict) -> dict`
**Location**: `src/agents/tree_structure_agent.py:13-59`

**Parameters:**
- `parsed_criteria` (dict): Output from CriteriaParserAgent

**Returns:**
```python
{
    "nodes": List[DecisionNode],
    "connections": List[NodeConnection],
    "metadata": {
        "root_node_id": str,
        "total_nodes": int,
        "depth": int
    }
}
```

**Key Features:**
- Optimizes question ordering (exclusionary criteria first)
- Generates specific outcome nodes with detailed reasons
- Creates fallback connections if LLM fails
- Supports multiple root nodes for complex trees

### 3. ValidationAgent

**Location**: `src/agents/validation_agent.py:7-357`

Validates tree structure and logic.

#### Methods

##### `validate(tree: dict, parsed_criteria: dict) -> dict`
**Location**: `src/agents/validation_agent.py:14-68`

**Parameters:**
- `tree` (dict): Decision tree from TreeStructureAgent
- `parsed_criteria` (dict): Original parsed criteria

**Returns:**
```python
{
    "is_valid": bool,
    "issues": List[ValidationIssue],
    "suggestions": List[str],
    "conflicts": List[dict]  # Detailed conflict information
}
```

**Validation Checks:**
- Logical consistency via LLM
- Completeness verification
- Ambiguity detection
- Edge case testing
- Conflict detection:
  - Contradictory paths
  - Circular dependencies
  - Redundant paths
  - Overlapping conditions

### 4. RefinementAgent

**Location**: `src/agents/refinement_agent.py:5-130`

Refines and optimizes the decision tree.

#### Methods

##### `refine(tree: dict, validation_results: dict) -> dict`
**Location**: `src/agents/refinement_agent.py:13-50`

**Parameters:**
- `tree` (dict): Original decision tree
- `validation_results` (dict): Results from ValidationAgent

**Returns:**
- `dict`: Refined decision tree with issues resolved

**Refinement Process:**
1. Resolve conflicts using ConflictResolver
2. Fix validation issues
3. Implement suggestions
4. Optimize structure

### 5. ConflictResolver

**Location**: `src/agents/conflict_resolver.py:7-293`

Specialized conflict resolution for decision trees.

#### Methods

##### `resolve_conflicts(tree: dict, conflicts: List[dict]) -> dict`
**Location**: `src/agents/conflict_resolver.py:16-70`

**Parameters:**
- `tree` (dict): Decision tree with conflicts
- `conflicts` (List[dict]): Conflicts from ValidationAgent

**Returns:**
```python
{
    "resolved_tree": dict,
    "resolutions": List[dict]  # Details of how conflicts were resolved
}
```

**Conflict Types Handled:**
- `CONTRADICTORY_PATHS`: Mutually exclusive paths leading to same outcome
- `CIRCULAR_DEPENDENCY`: Loops in decision flow
- `REDUNDANT_PATHS`: Multiple paths with identical logic
- `OVERLAPPING_CONDITIONS`: Partially overlapping criteria

## Service Layer

### DecisionTreeService

**Location**: `src/services/decision_tree_service.py:15-44`

Provides high-level async interface for the pipeline.

```python
class DecisionTreeService:
    async def process_new_criteria(self, document_id: str) -> dict
```

**Features:**
- Async/await support
- Repository pattern integration
- Event-driven architecture
- Error handling and logging

## Exception Hierarchy

**Location**: `src/core/exceptions.py:5-36`

```python
DecisionTreeGenerationError (base)
├── CriteriaParsingError
├── TreeStructureError
├── ValidationError
└── RefinementError
```

## Configuration

**Location**: `src/core/config.py:37-155`

The `ConfigManager` provides environment-specific configuration:

```python
config = ConfigManager.get_config()
model_info = ConfigManager.get_model_info()
```

**Environments:**
- `TEST`: Uses test models, reduced timeouts
- `DEVELOPMENT`: Standard models, verbose logging
- `PRODUCTION`: Optimized settings, minimal logging

## Usage Example

```python
from src.core.llm_client import LlmClient
from src.core.decision_tree_generator import DecisionTreeGenerator

# Initialize
llm_client = LlmClient(verbose=True)
generator = DecisionTreeGenerator(llm_client, verbose=True)

# Process document
with open("medical_criteria.txt", "r") as f:
    ocr_text = f.read()

try:
    decision_tree = generator.generate_decision_tree(ocr_text)
    print(f"Generated tree with {len(decision_tree['nodes'])} nodes")
except DecisionTreeGenerationError as e:
    print(f"Pipeline failed: {e}")
```
# Utilities and Helper Functions API Documentation

## Overview

This document covers the utility functions, helper modules, and supporting infrastructure that enable the prior authorization system's core functionality.

## Tree Traversal Utilities

### 1. SafeTreeTraverser

**Location**: `src/utils/tree_traversal.py:26-133`

Provides safe tree traversal with cycle detection and depth limiting.

```python
class SafeTreeTraverser:
    def __init__(self, max_depth: int = 100)
```

#### Configuration

##### `TraversalConfig`
**Location**: `src/utils/tree_traversal.py:18-23`

```python
@dataclass
class TraversalConfig:
    max_depth: int = 100
    track_paths: bool = True
    detect_cycles: bool = True
```

#### Key Methods

##### `traverse_tree(tree_dict: dict, visitor_func: Callable) -> Set[str]`
**Location**: `src/utils/tree_traversal.py:35-61`

Safely traverses tree structure with visitor pattern.

**Parameters:**
- `tree_dict` (dict): Tree structure with nodes and connections
- `visitor_func` (Callable): Function called for each node

**Returns:**
- `Set[str]`: Set of visited node IDs

**Features:**
- Automatic cycle detection
- Maximum depth enforcement
- Path tracking for debugging

##### `has_cycle() -> bool`
**Location**: `src/utils/tree_traversal.py:127-129`

Checks if cycles were detected during traversal.

### 2. Tree Structure Validation

##### `validate_tree_structure(tree_dict: dict) -> dict`
**Location**: `src/utils/tree_traversal.py:185-261`

Comprehensive tree structure validation.

**Parameters:**
- `tree_dict` (dict): Tree to validate

**Returns:**
```python
{
    "is_valid": bool,
    "errors": List[str],
    "warnings": List[str],
    "stats": {
        "total_nodes": int,
        "root_nodes": int,
        "leaf_nodes": int,
        "max_depth": int,
        "has_cycles": bool
    }
}
```

**Validation Checks:**
- Missing required fields
- Invalid node references
- Circular dependencies
- Orphaned nodes
- Multiple root nodes

### 3. Tree Navigation Functions

##### `find_root_nodes(tree_dict: dict) -> List[str]`
**Location**: `src/utils/tree_traversal.py:264-306`

Identifies root nodes (nodes with no incoming connections).

**Algorithm:**
1. Build incoming connections map
2. Find nodes with no incoming edges
3. Handle multiple roots gracefully

##### `detect_circular_references(tree_dict: dict) -> List[List[str]]`
**Location**: `src/utils/tree_traversal.py:309-365`

Detects all cycles in the tree structure.

**Returns:**
- `List[List[str]]`: List of cycles (each cycle is a list of node IDs)

**Algorithm:**
- Uses DFS with recursion stack
- Tracks all unique cycles
- Handles complex multi-node cycles

##### `find_all_paths(tree_dict: dict, start_node_id: str, end_node_id: str) -> List[List[str]]`
**Location**: `src/utils/tree_traversal.py:368-420`

Finds all possible paths between two nodes.

**Parameters:**
- `tree_dict` (dict): Tree structure
- `start_node_id` (str): Starting node ID
- `end_node_id` (str): Target node ID

**Returns:**
- `List[List[str]]`: All paths from start to end

**Features:**
- DFS-based path finding
- Cycle-safe with visited tracking
- Returns empty list if no path exists

### 4. Tree Rendering

##### `create_safe_tree_renderer(tree_dict: dict) -> str`
**Location**: `src/utils/tree_traversal.py:136-182`

Creates ASCII representation of tree structure.

**Features:**
- Handles missing nodes gracefully
- Shows node types and connections
- Indicates cycles and errors
- Depth-limited rendering

## JSON Utilities

### 1. JSON Sanitization

##### `sanitize_json_for_prompt(json_data: Union[dict, list, str]) -> str`
**Location**: `src/utils/json_utils.py:6-25`

Prepares JSON for LLM prompts by removing excessive indentation.

**Parameters:**
- `json_data`: JSON data (dict, list, or string)

**Returns:**
- `str`: Compact JSON string suitable for prompts

**Purpose:**
- Prevents cascading indentation in nested prompts
- Reduces token usage
- Maintains readability

### 2. JSON Normalization

##### `normalize_json_output(json_string: str) -> dict`
**Location**: `src/utils/json_utils.py:28-70`

Cleans and normalizes JSON output from LLMs.

**Parameters:**
- `json_string` (str): Raw JSON string from LLM

**Returns:**
- `dict`: Parsed and normalized JSON object

**Features:**
- Removes markdown code blocks
- Handles escaped characters
- Validates JSON structure
- Provides detailed error messages

**Error Handling:**
```python
try:
    normalized = normalize_json_output(llm_output)
except json.JSONDecodeError as e:
    print(f"Invalid JSON at position {e.pos}: {e.msg}")
```

## Performance Optimization

### TreeGenerationOptimizer

**Location**: `src/utils/performance.py:2-40`

Optimizes tree generation through batching and caching.

```python
class TreeGenerationOptimizer:
    def __init__(self)
```

#### Methods

##### `batch_process_criteria(criteria: List[Criterion]) -> List[DecisionNode]`
**Location**: `src/utils/performance.py:7-20`

Processes multiple criteria in parallel batches.

**Features:**
- Configurable batch size
- Progress tracking
- Error isolation per batch

##### `cache_common_patterns(patterns: Dict[str, Any]) -> Dict[str, DecisionNode]`
**Location**: `src/utils/performance.py:26-36`

Caches frequently used patterns for reuse.

**Parameters:**
- `patterns` (Dict[str, Any]): Common criteria patterns

**Returns:**
- `Dict[str, DecisionNode]`: Pre-generated nodes for patterns

## Advanced Criteria Parsing

### CriteriaParser

**Location**: `src/core/criteria_parser.py:15-320`

Advanced parsing utilities for medical criteria.

```python
class CriteriaParser:
    def __init__(self)
```

#### Enums

##### `CriterionType`
**Location**: `src/core/criteria_parser.py:5-9`

```python
class CriterionType(Enum):
    INCLUSION = "inclusion"
    EXCLUSION = "exclusion"
    DOCUMENTATION = "documentation"
```

##### `LogicalOperator`
**Location**: `src/core/criteria_parser.py:11-13`

```python
class LogicalOperator(Enum):
    AND = "AND"
    OR = "OR"
```

#### Key Methods

##### `parse_criteria_text(text: str) -> List[Criterion]`
**Location**: `src/core/criteria_parser.py:55-84`

Parses unstructured criteria text into structured format.

**Process:**
1. Split into individual criteria
2. Determine type for each criterion
3. Extract conditions and thresholds
4. Identify exceptions
5. Build relationships

##### `enhance_criteria_relationships(criteria: List[Criterion]) -> List[Criterion]`
**Location**: `src/core/criteria_parser.py:233-252`

Enhances criteria with relationship information.

**Features:**
- Groups related criteria
- Determines evaluation order
- Builds dependency map
- Optimizes for fail-fast evaluation

##### `_extract_thresholds(text: str) -> Dict[str, Any]`
**Location**: `src/core/criteria_parser.py:195-214`

Extracts numeric thresholds from criteria text.

**Patterns Detected:**
- Age limits: "≥18 years", "between 18-65"
- Lab values: "HbA1c ≥7.0%", "eGFR >30"
- Durations: "for at least 3 months"
- Frequencies: "2 or more episodes"

##### `_build_dependency_map(criteria: List[Criterion]) -> Dict[str, List[str]]`
**Location**: `src/core/criteria_parser.py:295-320`

Creates dependency graph between criteria.

**Returns:**
```python
{
    "criterion_id": ["dependent_criterion_1", "dependent_criterion_2"]
}
```

## Monitoring and Metrics

### 1. MetricsClient

**Location**: `src/monitoring/metrics.py:0-5`

Simple metrics collection interface.

```python
class MetricsClient:
    def gauge(self, metric_name: str, value: float)
    def increment(self, metric_name: str, count: int = 1)
```

### 2. TreeGenerationMetrics

**Location**: `src/monitoring/metrics.py:7-24`

Specialized metrics for tree generation.

```python
class TreeGenerationMetrics:
    def track_generation(self, tree: dict, duration: float)
    def track_llm_usage(self, model: str, tokens: int, duration: float)
```

#### Methods

##### `track_generation(tree: dict, duration: float)`
**Location**: `src/monitoring/metrics.py:11-15`

Records tree generation metrics:
- Node count
- Tree depth
- Generation time
- Connection complexity

##### `track_llm_usage(model: str, tokens: int, duration: float)`
**Location**: `src/monitoring/metrics.py:21-24`

Tracks LLM API usage:
- Model name
- Token consumption
- Response time
- Cost estimation

## Quality Assurance

### TreeQualityAssurance

**Location**: `src/quality_assurance/qa.py:5-64`

Comprehensive quality testing for generated trees.

```python
class TreeQualityAssurance:
    def run_comprehensive_tests(self, tree: dict, test_cases: List[dict]) -> dict
```

#### Methods

##### `run_comprehensive_tests(tree: dict, test_cases: List[dict]) -> dict`
**Location**: `src/quality_assurance/qa.py:9-17`

Runs full test suite on generated tree.

**Returns:**
```python
{
    "coverage": float,  # 0-100%
    "clinical_accuracy": dict,
    "performance": dict,
    "compliance": dict
}
```

##### `_test_clinical_accuracy(tree: dict, clinical_cases: List[dict]) -> dict`
**Location**: `src/quality_assurance/qa.py:23-52`

Tests tree against known clinical scenarios.

**Test Cases Include:**
- Standard approvals
- Standard denials
- Edge cases
- Exception scenarios

**Metrics:**
- Accuracy rate
- False positive rate
- False negative rate
- Decision path analysis

## Configuration Utilities

### ConfigManager

**Location**: `src/core/config.py:37-155`

Centralized configuration management.

#### Methods

##### `get_config() -> AppConfig`
**Location**: `src/core/config.py:60-99`

Returns environment-specific configuration.

**Configuration Hierarchy:**
1. Environment variables (highest priority)
2. Configuration files
3. Default values

##### `get_model_info() -> Dict[str, Any]`
**Location**: `src/core/config.py:129-155`

Returns model-specific information:
- Token limits
- Cost per token
- Feature support
- Optimal parameters

## Integration Patterns

### Error Recovery Pattern

```python
from src.utils.tree_traversal import SafeTreeTraverser, validate_tree_structure

# Validate before processing
validation = validate_tree_structure(tree_dict)
if not validation["is_valid"]:
    logger.error(f"Tree validation failed: {validation['errors']}")
    # Apply recovery logic
    
# Safe traversal with cycle detection
traverser = SafeTreeTraverser(max_depth=50)
visited = traverser.traverse_tree(tree_dict, process_node)
if traverser.has_cycle():
    logger.warning("Cycle detected in tree")
```

### Performance Optimization Pattern

```python
from src.utils.performance import TreeGenerationOptimizer
from src.monitoring.metrics import TreeGenerationMetrics

optimizer = TreeGenerationOptimizer()
metrics = TreeGenerationMetrics()

# Batch process for performance
nodes = optimizer.batch_process_criteria(criteria_list)

# Track metrics
metrics.track_generation(tree, generation_time)
```

### JSON Processing Pattern

```python
from src.utils.json_utils import sanitize_json_for_prompt, normalize_json_output

# Prepare for LLM
prompt_json = sanitize_json_for_prompt(complex_tree)

# Clean LLM output
try:
    clean_json = normalize_json_output(llm_response)
except json.JSONDecodeError as e:
    # Handle malformed JSON
    logger.error(f"JSON parsing failed: {e}")
```
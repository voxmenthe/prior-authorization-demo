# Visualization and Demo Components API Documentation

## Overview

The visualization and demo components provide interactive demonstrations of the prior authorization system, including real-time tree visualization, progress tracking, and session management.

## Demo Orchestration

### 1. DemoOrchestrator

**Location**: `src/demo/orchestrator.py:58-344`

Central coordinator for demo sessions, managing document processing and result aggregation.

```python
class DemoOrchestrator:
    def __init__(self, output_dir: str = "outputs", verbose: bool = False)
```

#### Data Classes

##### `DocumentResult`
**Location**: `src/demo/orchestrator.py:27-36`

```python
@dataclass
class DocumentResult:
    document_name: str
    success: bool
    tree: Optional[dict] = None
    error: Optional[str] = None
    processing_time: float = 0.0
    metrics: Optional[DocumentMetrics] = None
```

##### `DemoSession`
**Location**: `src/demo/orchestrator.py:40-55`

```python
@dataclass
class DemoSession:
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    documents_processed: List[DocumentResult] = field(default_factory=list)
    total_duration: float = 0.0
```

#### Key Methods

##### `start_session() -> str`
**Location**: `src/demo/orchestrator.py:85-91`

Initializes a new demo session.

**Returns:**
- `str`: Unique session ID

##### `process_document(document_path: str, session_id: str) -> DocumentResult`
**Location**: `src/demo/orchestrator.py:93-190`

Processes a single document through the pipeline with comprehensive tracking.

**Parameters:**
- `document_path` (str): Path to the document
- `session_id` (str): Current session ID

**Returns:**
- `DocumentResult`: Processing results with metrics

**Features:**
- Real-time progress visualization
- Detailed step tracking
- Error handling with graceful degradation
- Automatic tree and report saving

##### `process_multiple_documents(document_paths: List[str], session_id: str) -> List[DocumentResult]`
**Location**: `src/demo/orchestrator.py:192-223`

Batch processes multiple documents with progress tracking.

##### `get_session_summary(session_id: str) -> dict`
**Location**: `src/demo/orchestrator.py:331-344`

Generates comprehensive session statistics.

**Returns:**
```python
{
    "total_documents": int,
    "successful": int,
    "failed": int,
    "total_duration": float,
    "average_time": float,
    "documents": List[dict]
}
```

### 2. ProgressTracker

**Location**: `src/demo/tracker.py:60-385`

Tracks detailed metrics for each processing step.

```python
class ProgressTracker:
    def __init__(self)
```

#### Data Classes

##### `StepMetrics`
**Location**: `src/demo/tracker.py:15-26`

```python
@dataclass
class StepMetrics:
    step_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    status: str = "pending"  # pending, in_progress, completed, failed
    api_calls: int = 0
    tokens_used: int = 0
    custom_metrics: Dict[str, Any] = field(default_factory=dict)
```

##### `DocumentMetrics`
**Location**: `src/demo/tracker.py:30-57`

```python
@dataclass
class DocumentMetrics:
    document_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    total_duration: Optional[float] = None
    steps: Dict[str, StepMetrics] = field(default_factory=dict)
    current_step: Optional[str] = None
    status: str = "pending"
```

#### Key Methods

##### `track_step(context_manager) -> StepMetrics`
**Location**: `src/demo/tracker.py:134-152`

Context manager for automatic step tracking.

**Usage:**
```python
with tracker.track_step("criteria_parsing", "doc1") as step:
    # Process step
    step.api_calls += 1
    step.tokens_used += 100
```

##### `get_session_summary() -> dict`
**Location**: `src/demo/tracker.py:231-282`

Returns detailed session metrics including:
- Total/average processing times
- API usage statistics
- Step-by-step performance breakdown
- Document-level metrics

##### `export_metrics(output_dir: str)`
**Location**: `src/demo/tracker.py:349-385`

Exports metrics in multiple formats:
- JSON summary
- CSV for analysis
- Detailed logs

## Visualization Components

### 1. VisualPresenter

**Location**: `src/demo/presenter.py:52-508`

Rich terminal UI for interactive demonstrations.

```python
class VisualPresenter:
    def __init__(self, theme: str = "monokai")
```

#### Key Methods

##### `show_banner()`
**Location**: `src/demo/presenter.py:70-88`

Displays styled welcome banner with system information.

##### `show_pipeline_step(step_name: str, description: str, status: str)`
**Location**: `src/demo/presenter.py:90-107`

Shows current pipeline step with visual indicators.

**Parameters:**
- `step_name` (str): Step identifier
- `description` (str): Human-readable description
- `status` (str): "pending", "in_progress", "completed", "failed"

##### `show_decision_tree(tree_dict: dict, title: str)`
**Location**: `src/demo/presenter.py:157-214`

Renders decision tree in terminal with rich formatting.

**Features:**
- Hierarchical tree visualization
- Color-coded node types
- Connection annotations
- Metadata display

##### `show_processing_summary(results: List[DocumentResult])`
**Location**: `src/demo/presenter.py:334-380`

Displays comprehensive processing results table.

##### `show_session_metrics(metrics: dict)`
**Location**: `src/demo/presenter.py:382-406`

Shows detailed session performance metrics.

### 2. Enhanced Visualization

#### `UnicodeTreeRenderer`
**Location**: `src/demo/enhanced_visualizer.py:152-440`

Advanced tree rendering with Unicode box-drawing characters.

```python
class UnicodeTreeRenderer:
    def render_tree(self, tree_data: dict) -> str
```

##### Key Methods

##### `render_tree(tree_data: dict) -> str`
**Location**: `src/demo/enhanced_visualizer.py:159-293`

Renders tree with advanced formatting:
- Smart column layout
- Proper spacing and alignment
- Unicode connectors
- Node type indicators

#### `AgentInsightRenderer`
**Location**: `src/demo/enhanced_visualizer.py:56-149`

Displays agent reasoning and confidence levels.

```python
class AgentInsightRenderer:
    def create_thinking_panel(self, agent_name: str, thoughts: List[str], 
                             confidence: float) -> Panel
```

##### Methods

##### `create_thinking_panel(agent_name: str, thoughts: List[str], confidence: float) -> Panel`
**Location**: `src/demo/enhanced_visualizer.py:62-102`

Creates rich panel showing agent's reasoning process.

**Features:**
- Animated thinking indicators
- Confidence visualization
- Formatted thought bubbles

#### `RealTimeLayoutManager`
**Location**: `src/demo/enhanced_visualizer.py:443-604`

Manages dynamic terminal layouts for real-time updates.

```python
class RealTimeLayoutManager:
    def create_processing_layout() -> Layout
    def update_layout_components(layout: Layout, updates: dict)
```

##### Key Methods

##### `animate_processing_sequence(console: Console, tree_data: dict, steps: List[dict])`
**Location**: `src/demo/enhanced_visualizer.py:518-544`

Animates the tree generation process step-by-step.

### 3. Demo Flow Functions

#### `create_demo_processing_steps(tracker: ProgressTracker) -> List[dict]`
**Location**: `src/demo/enhanced_visualizer.py:607-706`

Generates structured demo steps with progress tracking integration.

**Returns:**
```python
[
    {
        "name": str,
        "agent": str,
        "description": str,
        "duration": float,
        "thoughts": List[str],
        "confidence": float,
        "tree_updates": dict
    }
]
```

## Integration Points

### 1. Main Demo Entry Point

**Location**: `demo.py:193-207`

```python
def _process_document_with_tracking(orchestrator, presenter, tracker, doc_path, session_id):
    """Process document with full visual tracking"""
```

### 2. Enhanced Demo Entry Point

**Location**: `enhanced_demo.py:668-696`

```python
def _process_document_with_enhanced_tracking(orchestrator, layout_manager, 
                                           insight_renderer, tree_renderer, 
                                           tracker, doc_path, session_id):
    """Process with enhanced visualizations"""
```

## Usage Examples

### Basic Demo Session

```python
from src.demo.orchestrator import DemoOrchestrator
from src.demo.presenter import VisualPresenter
from src.demo.tracker import ProgressTracker

# Initialize components
orchestrator = DemoOrchestrator(verbose=True)
presenter = VisualPresenter()
tracker = ProgressTracker()

# Start session
session_id = orchestrator.start_session()
tracker.start_session()

# Process document
result = orchestrator.process_document("criteria.txt", session_id)

# Show results
presenter.show_processing_summary([result])
presenter.show_session_metrics(tracker.get_session_summary())
```

### Enhanced Visualization Demo

```python
from src.demo.enhanced_visualizer import (
    UnicodeTreeRenderer, 
    AgentInsightRenderer,
    RealTimeLayoutManager
)

# Initialize enhanced components
tree_renderer = UnicodeTreeRenderer()
insight_renderer = AgentInsightRenderer()
layout_manager = RealTimeLayoutManager()

# Create processing layout
layout = layout_manager.create_processing_layout()

# Animate processing
steps = create_demo_processing_steps(tracker)
layout_manager.animate_processing_sequence(console, tree_data, steps)
```

## Terminal UI Components

### Color Schemes

**Location**: `src/demo/presenter.py:27-49`

```python
class Colors:
    PRIMARY = "#00D9FF"
    SUCCESS = "#00FF88"
    WARNING = "#FFD700"
    ERROR = "#FF3366"
    INFO = "#8B8BFF"
    # ... more colors
```

### Tree Node Styles

**Location**: `src/demo/enhanced_visualizer.py:28-53`

```python
@dataclass
class TreeNodeStyle:
    box_color: str
    text_color: str
    icon: str
    prefix: str = ""
```

## Output Formats

### Session Report

**Location**: `src/demo/orchestrator.py:283-329`

```json
{
    "session_id": "20240627_123456",
    "start_time": "2024-06-27T12:34:56",
    "end_time": "2024-06-27T12:45:00",
    "total_duration": 604.5,
    "documents_processed": [...],
    "summary": {
        "total": 3,
        "successful": 2,
        "failed": 1
    }
}
```

### Metrics Export

**Location**: `src/demo/tracker.py:349-385`

Exports include:
- `metrics_summary.json`: High-level statistics
- `step_details.csv`: Detailed step timing
- `api_usage.json`: LLM API consumption
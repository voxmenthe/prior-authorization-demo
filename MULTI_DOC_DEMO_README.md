# Multi-Document Demo Scripts

Two simplified demo scripts showcasing multi-document processing capabilities for prior authorization decision trees.

## Scripts

### 1. `multi_doc_demo.py` - Basic Multi-Document Demo
A streamlined demo focusing on core multi-document functionality.

**Features:**
- Process multiple related documents together
- Automatic document grouping by pattern matching
- Single documents processed through same pipeline
- Simple, clean output

**Commands:**
```bash
# Run the demo
python multi_doc_demo.py run

# List available examples
python multi_doc_demo.py list-examples

# Show multi-document info
python multi_doc_demo.py info

# Test components (no API key needed)
python multi_doc_demo.py test
```

### 2. `enhanced_multi_doc_demo.py` - Enhanced Visual Demo
An enhanced version with rich visualizations and animations.

**Features:**
- Real-time processing visualization
- Document relationship mapping
- Animated processing steps
- Visual merge process demonstration

**Commands:**
```bash
# Run with full animations
python enhanced_multi_doc_demo.py run

# Run without animations
python enhanced_multi_doc_demo.py run --no-animate

# Compare single vs multi-document
python enhanced_multi_doc_demo.py compare
```

## Examples

Both demos include two examples:

1. **Dupixent (Multi-Document)**
   - `dupixent_insurance_policy.txt` - Insurance coverage criteria
   - `dupixent_clinical_guidelines.txt` - Clinical usage guidelines
   - Demonstrates automatic document grouping and criteria merging

2. **Jardiance (Single Document)**
   - `jardiance_criteria.txt` - Comprehensive criteria in one file
   - Shows how single documents work through multi-doc pipeline

## Requirements

- Set `GOOGLE_API_KEY` environment variable for full processing
- Python 3.8+ with dependencies installed
- Multi-document processing is enabled by default in these demos

## Output

Results are saved to:
- `outputs/multi_doc/` - Basic demo output
- `outputs/enhanced_multi_doc/` - Enhanced demo output

Each run creates JSON files with the unified decision trees.

## Key Concepts

1. **Document Grouping**: Files are automatically grouped by naming patterns (e.g., `drugname_doctype.txt`)

2. **Relationship Mapping**: Documents are linked based on their types (insurance → guidelines)

3. **Unified Processing**: Both single and multiple documents use the same pipeline

4. **Merge Strategy**: Supplementary criteria are appended to the primary decision tree

## Testing Without API Key

To test the multi-document components without needing an API key:

```bash
python multi_doc_demo.py test
```

This verifies:
- Document set identification
- Pattern matching
- Component initialization
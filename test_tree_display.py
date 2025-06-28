#!/usr/bin/env python3
"""
Test script to verify decision tree display functionality
"""

from pathlib import Path
from src.demo.orchestrator import DemoOrchestrator
from src.demo.presenter import VisualPresenter

def test_tree_display():
    """Test that generated decision trees are displayed correctly"""
    
    # Initialize components
    orchestrator = DemoOrchestrator(output_dir="test_outputs", verbose=True)
    presenter = VisualPresenter()
    
    # Test with a small example document
    test_doc = Path("examples/jardiance_criteria.txt")
    
    if not test_doc.exists():
        print(f"❌ Test document not found: {test_doc}")
        return
    
    print(f"📄 Processing: {test_doc}")
    print("=" * 80)
    
    # Process the document
    result = orchestrator.process_document(str(test_doc))
    
    print(f"\n📊 Processing Result:")
    print(f"  - Success: {result.success}")
    print(f"  - Processing time: {result.processing_time:.2f}s")
    
    if result.success and result.decision_tree:
        print(f"  - Decision tree type: {type(result.decision_tree)}")
        print(f"  - Has 'nodes' key: {'nodes' in result.decision_tree}")
        
        if 'nodes' in result.decision_tree:
            nodes = result.decision_tree['nodes']
            print(f"  - Nodes type: {type(nodes)}")
            print(f"  - Number of nodes: {len(nodes) if isinstance(nodes, dict) else 'N/A'}")
            
            if 'start_node' in result.decision_tree:
                print(f"  - Start node: {result.decision_tree['start_node']}")
        
        print("\n🌳 Displaying Decision Tree:")
        print("=" * 80)
        presenter.show_decision_tree(result.decision_tree, result.document_name)
        
    else:
        if result.error:
            print(f"  - Error: {result.error}")
        print("\n❌ No decision tree was generated")

if __name__ == "__main__":
    test_tree_display()
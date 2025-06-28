#!/usr/bin/env python3
"""
Debug script to examine the actual structure of the decision tree data
"""

import json
from pathlib import Path
from src.demo.orchestrator import DemoOrchestrator
from src.core.decision_tree_generator import DecisionTreeGenerator

def debug_tree_structure():
    """Debug the tree structure returned by the orchestrator"""
    
    print("🔍 Debugging decision tree data structure...")
    
    # Test document
    jardiance_path = Path("examples/jardiance_criteria.txt")
    if not jardiance_path.exists():
        print("❌ Test document not found")
        return
    
    print(f"📄 Processing: {jardiance_path}")
    
    # Test orchestrator
    orchestrator = DemoOrchestrator(output_dir="debug_outputs", verbose=True)
    result = orchestrator.process_document(str(jardiance_path))
    
    print(f"\n📊 Result success: {result.success}")
    print(f"🔧 Result type: {type(result.decision_tree)}")
    
    if result.decision_tree:
        print(f"📦 Decision tree type: {type(result.decision_tree)}")
        print(f"📏 Decision tree length/keys: ", end="")
        
        if isinstance(result.decision_tree, str):
            print(f"String length: {len(result.decision_tree)}")
            print("🧵 First 200 chars of string:")
            print(repr(result.decision_tree[:200]))
            
            # Try to parse as JSON
            try:
                parsed = json.loads(result.decision_tree)
                print(f"✅ Successfully parsed as JSON")
                print(f"📦 Parsed type: {type(parsed)}")
                print(f"🔑 Keys: {list(parsed.keys()) if isinstance(parsed, dict) else 'Not a dict'}")
                
                if isinstance(parsed, dict) and 'nodes' in parsed:
                    nodes = parsed['nodes']
                    print(f"🌳 Nodes type: {type(nodes)}")
                    if isinstance(nodes, dict):
                        print(f"🔑 Node IDs: {list(nodes.keys())}")
                        print(f"📊 Number of nodes: {len(nodes)}")
                        
                        # Show first node structure
                        if nodes:
                            first_node_id = list(nodes.keys())[0]
                            first_node = nodes[first_node_id]
                            print(f"🎯 First node ({first_node_id}):")
                            print(json.dumps(first_node, indent=2))
                    elif isinstance(nodes, str):
                        print(f"⚠️ Nodes is a string: {repr(nodes[:100])}")
                
            except json.JSONDecodeError as e:
                print(f"❌ Failed to parse as JSON: {e}")
        
        elif isinstance(result.decision_tree, dict):
            print(f"Dict keys: {list(result.decision_tree.keys())}")
            
            if 'nodes' in result.decision_tree:
                nodes = result.decision_tree['nodes']
                print(f"🌳 Nodes type: {type(nodes)}")
                if isinstance(nodes, dict):
                    print(f"🔑 Node IDs: {list(nodes.keys())}")
                elif isinstance(nodes, str):
                    print(f"⚠️ Nodes is a string: {repr(nodes[:100])}")
            
            # Show full structure
            print("🔍 Full structure:")
            print(json.dumps(result.decision_tree, indent=2, default=str))
        
        else:
            print(f"❓ Unknown type: {type(result.decision_tree)}")
            print(f"📋 Content: {repr(result.decision_tree)}")

if __name__ == "__main__":
    debug_tree_structure()
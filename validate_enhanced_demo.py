#!/usr/bin/env python3
"""
Validation script for enhanced demo features without requiring LLM processing
"""

import json
from src.demo.enhanced_visualizer import UnicodeTreeRenderer, AgentInsightRenderer
from rich.console import Console

def test_actual_tree_data_handling():
    """Test with actual tree data format that might come from LLM."""
    console = Console()
    renderer = UnicodeTreeRenderer()
    
    # Test 1: Normal dictionary format
    normal_tree = {
        "nodes": {
            "root": {
                "id": "root",
                "type": "question",
                "question": "Patient age >= 18 years?",
                "connections": {"true": "diagnosis", "false": "deny"}
            },
            "diagnosis": {
                "id": "diagnosis",
                "type": "question", 
                "question": "Valid diagnosis?",
                "connections": {"true": "approve", "false": "deny"}
            },
            "approve": {
                "id": "approve",
                "type": "outcome",
                "decision": "APPROVE"
            },
            "deny": {
                "id": "deny",
                "type": "outcome",
                "decision": "DENY"
            }
        }
    }
    
    console.print("🧪 Test 1: Normal dictionary format")
    result = renderer.render_tree(normal_tree)
    console.print(result)
    
    # Test 2: JSON string format (problematic case)
    json_string_tree = {
        "nodes": json.dumps({
            "root": {
                "id": "root",
                "type": "question",
                "question": "Age check?",
                "connections": {"true": "approve", "false": "deny"}
            },
            "approve": {
                "id": "approve",
                "type": "outcome",
                "decision": "APPROVED"
            },
            "deny": {
                "id": "deny", 
                "type": "outcome",
                "decision": "DENIED"
            }
        })
    }
    
    console.print("\n🧪 Test 2: JSON string format (fixed)")
    result = renderer.render_tree(json_string_tree)
    console.print(result)
    
    # Test 3: Invalid format
    invalid_tree = {
        "nodes": "not valid json at all"
    }
    
    console.print("\n🧪 Test 3: Invalid format (error handling)")
    result = renderer.render_tree(invalid_tree)
    console.print(result)
    
    # Test 4: Wrong type
    wrong_type_tree = {
        "nodes": ["this", "is", "a", "list"]
    }
    
    console.print("\n🧪 Test 4: Wrong type format (error handling)")
    result = renderer.render_tree(wrong_type_tree)
    console.print(result)

def test_agent_insights():
    """Test agent insight rendering."""
    console = Console()
    renderer = AgentInsightRenderer(console)
    
    console.print("\n🧪 Testing Agent Insights:")
    
    agents = [
        ("CriteriaParser", "Parsing criteria", "Found key eligibility rules", 0.95),
        ("TreeStructure", "Building tree", "Created optimal structure", 0.82),
        ("Validation", "Checking logic", "All paths validated", 0.91),
        ("Refinement", "Optimizing", "Improved readability", 0.77)
    ]
    
    for agent, step, reasoning, confidence in agents:
        panel = renderer.create_thinking_panel(agent, step, reasoning, confidence)
        console.print(panel)

if __name__ == "__main__":
    console = Console()
    console.print("[bold bright_green]🧪 Enhanced Demo Validation Tests[/bold bright_green]\n")
    
    test_actual_tree_data_handling()
    test_agent_insights()
    
    console.print("\n[bold bright_green]✅ All validation tests completed![/bold bright_green]")
    console.print("[dim]The enhanced demo should now handle various data formats correctly.[/dim]")
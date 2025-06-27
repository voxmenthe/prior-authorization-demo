#!/usr/bin/env python3
"""
Quick test script for the enhanced demo functionality
"""

from src.demo.enhanced_visualizer import (
    UnicodeTreeRenderer, 
    AgentInsightRenderer,
    create_demo_processing_steps
)
from rich.console import Console

def test_tree_renderer():
    """Test the Unicode tree renderer with sample data."""
    console = Console()
    renderer = UnicodeTreeRenderer()
    
    # Sample tree data
    sample_tree = {
        "nodes": {
            "root": {
                "id": "root",
                "type": "question",
                "question": "Patient age >= 18 years?",
                "connections": {"true": "diagnosis", "false": "deny_age"}
            },
            "diagnosis": {
                "id": "diagnosis", 
                "type": "question",
                "question": "Valid diagnosis confirmed?",
                "connections": {"true": "approve", "false": "deny_diagnosis"}
            },
            "deny_age": {
                "id": "deny_age",
                "type": "outcome",
                "decision": "DENY: Patient under 18"
            },
            "approve": {
                "id": "approve",
                "type": "outcome", 
                "decision": "APPROVE: All criteria met"
            },
            "deny_diagnosis": {
                "id": "deny_diagnosis",
                "type": "outcome",
                "decision": "DENY: Invalid diagnosis"
            }
        }
    }
    
    console.print("🧪 Testing Unicode Tree Renderer:")
    tree_visual = renderer.render_tree(sample_tree, highlight_node="diagnosis")
    console.print(tree_visual)

def test_agent_renderer():
    """Test the agent insight renderer."""
    console = Console()
    renderer = AgentInsightRenderer(console)
    
    console.print("\n🧪 Testing Agent Insight Renderer:")
    
    panel = renderer.create_thinking_panel(
        "CriteriaParser",
        "Extracting eligibility criteria", 
        "Analyzing document structure and identifying key decision points",
        confidence=0.87,
        data_points=[
            "Found 8 eligibility criteria",
            "Identified age requirement",
            "Located insurance validation rules"
        ]
    )
    
    console.print(panel)

def test_processing_steps():
    """Test the demo processing steps."""
    console = Console()
    
    console.print("\n🧪 Testing Processing Steps Data:")
    steps = create_demo_processing_steps()
    
    for i, step in enumerate(steps):
        console.print(f"Step {i+1}: {step['agent_info']['name']} - {step['agent_info']['step']}")

if __name__ == "__main__":
    test_tree_renderer()
    test_agent_renderer() 
    test_processing_steps()
    
    print("\n✅ All enhanced demo components tested successfully!")
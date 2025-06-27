#!/usr/bin/env python3
"""
Decision Tree Visualizer using Graphviz

Creates static visualization images from decision tree JSON files.
"""

import json
import argparse
from pathlib import Path
import subprocess


def parse_tree_data(tree_json: dict) -> dict:
    """Parse the tree structure from JSON format."""
    if "decision_tree" in tree_json:
        nodes_data = tree_json["decision_tree"]["nodes"]
        if isinstance(nodes_data, str):
            nodes = json.loads(nodes_data)
        else:
            nodes = nodes_data
    else:
        nodes = tree_json.get("nodes", [])
    
    return {"nodes": nodes}


def generate_dot_content(tree_data: dict, title: str = "Decision Tree") -> str:
    """Generate DOT format content for Graphviz."""
    nodes = tree_data["nodes"]
    
    dot_lines = [
        "digraph DecisionTree {",
        "    rankdir=TB;",
        "    node [shape=box, style=filled];",
        f'    labelloc="t";',
        f'    label="{title}";',
        ""
    ]
    
    # Add nodes
    for node in nodes:
        node_id = node["id"]
        node_type = node.get("type", "unknown").lower()
        
        if node_type == "question":
            question = node.get("question", "Unknown Question")
            # Wrap long questions
            wrapped_question = "\\n".join([question[i:i+40] for i in range(0, len(question), 40)])
            dot_lines.append(f'    {node_id} [label="{wrapped_question}", fillcolor=lightblue];')
        elif node_type == "outcome":
            outcome = node.get("outcome", "Unknown Outcome")
            # Wrap long outcomes
            wrapped_outcome = "\\n".join([outcome[i:i+40] for i in range(0, len(outcome), 40)])
            dot_lines.append(f'    {node_id} [label="{wrapped_outcome}", fillcolor=lightgreen];')
        else:
            label = node.get("question", node.get("outcome", node_id))
            wrapped_label = "\\n".join([label[i:i+40] for i in range(0, len(label), 40)])
            dot_lines.append(f'    {node_id} [label="{wrapped_label}", fillcolor=lightgray];')
    
    dot_lines.append("")
    
    # Add connections
    for node in nodes:
        node_id = node["id"]
        connections = node.get("connections", [])
        
        for connection in connections:
            target = connection.get("target_node_id")
            condition = connection.get("condition", "")
            condition_value = connection.get("condition_value", "")
            
            if target:
                label = ""
                if condition and condition_value:
                    label = f"{condition_value}"
                
                if label:
                    dot_lines.append(f'    {node_id} -> {target} [label="{label}"];')
                else:
                    dot_lines.append(f'    {node_id} -> {target};')
    
    dot_lines.append("}")
    return "\n".join(dot_lines)


def create_visualization(json_file: Path, output_dir: Path, format: str = "png"):
    """Create visualization from a single JSON file."""
    with open(json_file, 'r') as f:
        tree_json = json.load(f)
    
    tree_data = parse_tree_data(tree_json)
    title = json_file.stem.replace('_', ' ').title()
    dot_content = generate_dot_content(tree_data, title)
    
    # Create DOT file
    dot_file = output_dir / f"{json_file.stem}.dot"
    with open(dot_file, 'w') as f:
        f.write(dot_content)
    
    # Generate image
    output_file = output_dir / f"{json_file.stem}.{format}"
    try:
        subprocess.run([
            "dot", f"-T{format}", str(dot_file), "-o", str(output_file)
        ], check=True, capture_output=True)
        print(f"✅ Created: {output_file}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error creating {output_file}: {e.stderr.decode()}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Visualize decision trees from JSON files")
    parser.add_argument("input", nargs="?", default="outputs/decision_trees", 
                       help="Input JSON file or directory (default: outputs/decision_trees)")
    parser.add_argument("-o", "--output", default="outputs/visualizations",
                       help="Output directory (default: outputs/visualizations)")
    parser.add_argument("-f", "--format", default="png", choices=["png", "svg", "pdf"],
                       help="Output format (default: png)")
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if input_path.is_file():
        # Single file
        create_visualization(input_path, output_dir, args.format)
    elif input_path.is_dir():
        # Directory of JSON files
        json_files = list(input_path.glob("*.json"))
        if not json_files:
            print(f"No JSON files found in {input_path}")
            return
        
        print(f"Found {len(json_files)} JSON files")
        success_count = 0
        
        for json_file in json_files:
            if create_visualization(json_file, output_dir, args.format):
                success_count += 1
        
        print(f"\n🎯 Successfully created {success_count}/{len(json_files)} visualizations")
        print(f"📁 Output directory: {output_dir}")
    else:
        print(f"Error: {input_path} not found")


if __name__ == "__main__":
    main()
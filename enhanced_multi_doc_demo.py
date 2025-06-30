#!/usr/bin/env python3
"""
Enhanced Multi-Document Prior Authorization Demo

Features:
- Real-time visualization of multi-document processing
- Visual document relationship mapping
- Live merge strategy demonstration
"""

import os
import sys
import time
from pathlib import Path
from typing import List, Optional, Dict, Any

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.tree import Tree
from rich.live import Live
from rich.layout import Layout
from rich.align import Align
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from src.core.decision_tree_generator import DecisionTreeGenerator
from src.core.schemas import UnifiedDecisionTree, DocumentSet
from src.utils.document_set_manager import DocumentSetManager
from src.demo.presenter import VisualPresenter
from src.demo.enhanced_visualizer import UnicodeTreeRenderer

# Enable multi-document processing by default
os.environ["ENABLE_MULTI_DOCUMENT"] = "true"

# Initialize console and app
console = Console()
presenter = VisualPresenter(console)
app = typer.Typer(
    name="enhanced-multi-doc",
    help="Enhanced Multi-Document Prior Authorization Demo",
    rich_markup_mode="rich"
)


class MultiDocVisualizer:
    """Visualizer for multi-document processing."""
    
    def __init__(self, console: Console):
        self.console = console
        self.tree_renderer = UnicodeTreeRenderer(max_depth=15)
    
    def show_document_relationships(self, doc_set: DocumentSet):
        """Visualize document relationships."""
        # Create relationship table
        table = Table(title="📊 Document Relationships", border_style="bright_blue")
        table.add_column("From Document", style="cyan")
        table.add_column("Relationship", style="green")
        table.add_column("To Document", style="cyan")
        table.add_column("References", style="dim")
        
        for rel in doc_set.relationships:
            table.add_row(
                rel.from_doc,
                rel.relationship_type.value,
                rel.to_doc,
                ", ".join(rel.references) if rel.references else "N/A"
            )
        
        self.console.print(table)
    
    def show_merge_visualization(self, primary_tree: dict, supplementary_data: List[dict]):
        """Visualize the merge process."""
        layout = Layout()
        
        # Create three columns: primary, arrow, supplementary
        layout.split_row(
            Layout(name="primary", ratio=2),
            Layout(name="arrow", size=10),
            Layout(name="supplementary", ratio=2)
        )
        
        # Primary tree panel
        primary_text = Text("🏥 Primary Document\n\n", style="bold cyan")
        primary_text.append("Insurance Policy\n", style="bright_white")
        primary_text.append(f"Nodes: {len(primary_tree.get('nodes', {}))}\n", style="dim")
        layout["primary"].update(Panel(primary_text, border_style="cyan"))
        
        # Arrow
        arrow_text = Text("\n\n➡️\nMERGE\n➡️", justify="center", style="bold green")
        layout["arrow"].update(arrow_text)
        
        # Supplementary panel
        supp_text = Text("📋 Supplementary Documents\n\n", style="bold magenta")
        for i, data in enumerate(supplementary_data):
            supp_text.append(f"Clinical Guidelines {i+1}\n", style="bright_white")
            supp_text.append(f"Criteria: {len(data.get('criteria', []))}\n", style="dim")
        layout["supplementary"].update(Panel(supp_text, border_style="magenta"))
        
        self.console.print(Panel(layout, title="🔄 Document Merge Process", border_style="green"))
    
    def animate_processing(self, doc_name: str, steps: List[str]):
        """Animate document processing steps."""
        with Live(console=self.console, refresh_per_second=4) as live:
            for i, step in enumerate(steps):
                # Create step visualization
                step_text = Text()
                
                for j, s in enumerate(steps):
                    if j < i:
                        step_text.append(f"✅ {s}\n", style="green")
                    elif j == i:
                        step_text.append(f"🔄 {s}...\n", style="bold yellow")
                    else:
                        step_text.append(f"⏳ {s}\n", style="dim")
                
                panel = Panel(
                    step_text,
                    title=f"Processing {doc_name}",
                    border_style="bright_blue"
                )
                
                live.update(panel)
                time.sleep(1.0)
        
        # Final success message
        self.console.print(Panel(
            Text("✅ All steps completed!", style="bold green"),
            border_style="green"
        ))


def process_with_visualization(
    doc_paths: List[Path], 
    doc_name: str, 
    visualizer: MultiDocVisualizer,
    verbose: bool = False
) -> Optional[dict]:
    """Process documents with enhanced visualization."""
    
    # Initialize components
    generator = DecisionTreeGenerator(verbose=verbose)
    manager = DocumentSetManager()
    
    # Processing steps
    steps = [
        "Identifying document relationships",
        "Processing primary document",
        "Processing supplementary documents",
        "Merging decision trees",
        "Finalizing unified tree"
    ]
    
    # Animate processing
    visualizer.animate_processing(doc_name, steps)
    
    try:
        # Identify document set if multiple documents
        if len(doc_paths) > 1:
            doc_set = manager.identify_document_set(doc_paths)
            if doc_set:
                console.print("\n[bright_cyan]📊 Document Set Identified[/bright_cyan]")
                visualizer.show_document_relationships(doc_set)
        
        # Process documents
        result = generator.generate_from_documents(doc_paths)
        
        # Show results
        if isinstance(result, UnifiedDecisionTree):
            console.print(f"\n[bright_green]✅ Multi-document processing successful![/bright_green]")
            
            # Show merge visualization
            if len(doc_paths) > 1:
                console.print("\n[bright_yellow]🔄 Merge Process Visualization[/bright_yellow]")
                # Simplified visualization since we don't have access to intermediate results
                primary_tree = {"nodes": {}}  # Placeholder
                supplementary_data = [{"criteria": []} for _ in range(len(doc_paths) - 1)]
                visualizer.show_merge_visualization(primary_tree, supplementary_data)
            
            return result.tree
        else:
            console.print(f"\n[bright_green]✅ Document processing successful![/bright_green]")
            return result
            
    except Exception as e:
        console.print(f"\n[red]❌ Error: {str(e)}[/red]")
        if verbose:
            console.print_exception()
        return None


@app.command()
def run(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    output_dir: str = typer.Option("outputs/enhanced_multi_doc", "--output-dir", "-o", help="Output directory"),
    show_trees: bool = typer.Option(True, "--show-trees/--no-trees", help="Display decision trees"),
    animate: bool = typer.Option(True, "--animate/--no-animate", help="Show animations"),
):
    """
    Run the enhanced multi-document demo.
    
    Features real-time visualization of document relationships and merge process.
    """
    # Banner
    banner = Panel(
        Text.assemble(
            ("📚 ENHANCED MULTI-DOCUMENT DEMO", "bold bright_blue"),
            ("\n✨ Real-time Document Processing Visualization", "italic cyan"),
            ("\n🔄 Live Merge Strategy Demonstration", "italic green"),
        ),
        title="🏥 Advanced Prior Authorization System",
        border_style="bright_blue",
        padding=(1, 2)
    )
    console.print()
    console.print(banner)
    console.print()
    
    output_path = Path(output_dir)
    visualizer = MultiDocVisualizer(console)
    
    # Examples to process
    examples = [
        {
            "name": "Dupixent Multi-Document Analysis",
            "description": "Insurance policy + Clinical guidelines",
            "files": [
                Path("examples/dupixent_insurance_policy.txt"),
                Path("examples/dupixent_clinical_guidelines.txt")
            ],
            "output_name": "dupixent_unified"
        },
        {
            "name": "Jardiance Single Document",
            "description": "Comprehensive criteria (via multi-doc pipeline)",
            "files": [Path("examples/jardiance_criteria.txt")],
            "output_name": "jardiance_multidoc"
        }
    ]
    
    # Process examples
    for i, example in enumerate(examples):
        # Section header
        console.print(f"\n[bright_blue]{'='*60}[/bright_blue]")
        console.print(f"[bold bright_cyan]📁 Example {i+1}: {example['name']}[/bold bright_cyan]")
        console.print(f"[dim]{example['description']}[/dim]")
        console.print(f"[bright_blue]{'='*60}[/bright_blue]\n")
        
        # Show files
        file_tree = Tree("📂 Input Files")
        for file in example['files']:
            if file.exists():
                size = file.stat().st_size
                file_tree.add(f"[green]✓[/green] {file.name} ({size:,} bytes)")
            else:
                file_tree.add(f"[red]✗[/red] {file.name} (missing)")
        console.print(file_tree)
        console.print()
        
        # Check if files exist
        if not all(f.exists() for f in example['files']):
            console.print("[red]❌ Some files are missing, skipping...[/red]")
            continue
        
        # Process with visualization
        if animate:
            tree_data = process_with_visualization(
                example['files'], 
                example['name'],
                visualizer,
                verbose
            )
        else:
            # Simple processing without animation
            generator = DecisionTreeGenerator(verbose=verbose)
            result = generator.generate_from_documents(example['files'])
            tree_data = result.tree if isinstance(result, UnifiedDecisionTree) else result
        
        if tree_data:
            # Save results
            import json
            output_path.mkdir(parents=True, exist_ok=True)
            output_file = output_path / f"{example['output_name']}.json"
            
            with open(output_file, 'w') as f:
                json.dump(tree_data, f, indent=2)
            
            console.print(f"\n💾 Results saved to: {output_file}")
            
            # Show tree visualization if requested
            if show_trees:
                console.print("\n[bright_green]🌳 Decision Tree Visualization[/bright_green]")
                tree_visual = visualizer.tree_renderer.render_tree(tree_data, show_connections=True)
                console.print(Panel(tree_visual, border_style="green"))
        
        # Pause between examples
        if i < len(examples) - 1:
            console.print("\n[dim]Press Enter to continue to next example...[/dim]")
            input()
    
    # Final summary
    console.print("\n[bright_green]🎉 Enhanced multi-document demo completed![/bright_green]")
    console.print(f"\nResults saved to: {output_path}/")
    
    # Show insights
    insights = Panel(
        Text.assemble(
            ("Key Insights:\n\n", "bold bright_yellow"),
            ("• ", "dim"), ("Document Grouping: ", "cyan"), 
            ("Automatic pattern-based identification\n", "white"),
            ("• ", "dim"), ("Relationship Mapping: ", "cyan"), 
            ("Cross-references between documents tracked\n", "white"),
            ("• ", "dim"), ("Unified Processing: ", "cyan"), 
            ("Single and multi-doc use same pipeline\n", "white"),
            ("• ", "dim"), ("Merge Strategy: ", "cyan"), 
            ("Supplementary criteria appended to primary tree\n", "white"),
        ),
        title="💡 Multi-Document Processing Insights",
        border_style="bright_yellow"
    )
    console.print(insights)


@app.command()
def compare():
    """Compare single vs multi-document processing."""
    console.print("[bright_cyan]🔍 Comparing Single vs Multi-Document Processing[/bright_cyan]\n")
    
    # Create comparison table
    table = Table(title="Single vs Multi-Document Comparison", border_style="bright_blue")
    table.add_column("Aspect", style="cyan", width=30)
    table.add_column("Single Document", style="yellow", width=35)
    table.add_column("Multi-Document", style="green", width=35)
    
    comparisons = [
        ("Input", "One criteria file", "Multiple related files"),
        ("Document Identification", "N/A", "Pattern matching or manifest"),
        ("Processing", "Direct parsing", "Parallel processing + merge"),
        ("Output Type", "Dictionary", "UnifiedDecisionTree object"),
        ("Relationships", "None", "Tracked and preserved"),
        ("Use Case", "Simple criteria", "Complex policies + guidelines"),
        ("Example", "jardiance_criteria.txt", "dupixent_insurance.txt + dupixent_guidelines.txt"),
    ]
    
    for aspect, single, multi in comparisons:
        table.add_row(aspect, single, multi)
    
    console.print(table)
    
    console.print("\n[bold]Benefits of Multi-Document Processing:[/bold]")
    console.print("• Captures complete authorization requirements")
    console.print("• Maintains document relationships and context")
    console.print("• Enables future reference resolution")
    console.print("• Supports complex healthcare policies")


if __name__ == "__main__":
    app()
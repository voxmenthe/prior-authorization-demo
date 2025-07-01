#!/usr/bin/env python3
"""
Multi-Document Prior Authorization Decision Tree Demo

Simplified demo showcasing multi-document processing with:
- Dupixent multi-document example (insurance policy + clinical guidelines)
- Jardiance single document example (processed through multi-doc pipeline)
"""

import os
import sys
import time
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from src.core.decision_tree_generator import DecisionTreeGenerator
from src.core.schemas import UnifiedDecisionTree
from src.demo.presenter import VisualPresenter

# Enable multi-document processing by default
os.environ["ENABLE_MULTI_DOCUMENT"] = "true"

# Initialize console and app
console = Console()
presenter = VisualPresenter(console)
app = typer.Typer(
    name="multi-doc-demo",
    help="Multi-Document Prior Authorization Demo",
    rich_markup_mode="rich"
)


def show_multi_doc_banner():
    """Show banner for multi-document demo."""
    banner_text = Text.assemble(
        ("📚 MULTI-DOCUMENT DECISION TREE DEMO", "bold bright_blue"),
        ("\n✨ Processing related documents together", "italic cyan"),
    )
    
    banner_panel = Panel(
        banner_text,
        title="🏥 Prior Authorization with Multi-Doc Support",
        title_align="center",
        border_style="bright_blue",
        padding=(1, 2)
    )
    
    console.print()
    console.print(banner_panel)
    console.print()


def process_documents(doc_paths: List[Path], doc_name: str, verbose: bool = False) -> Optional[dict]:
    """Process documents through multi-document pipeline."""
    try:
        generator = DecisionTreeGenerator(verbose=verbose)
        
        # Process documents (works for both single and multiple)
        result = generator.generate_from_documents(doc_paths)
        
        # Display results based on type
        if isinstance(result, UnifiedDecisionTree):
            console.print(f"\n[bright_green]✅ Multi-document processing completed for {doc_name}[/bright_green]")
            console.print(f"   • Processed {len(result.source_documents)} documents")
            console.print(f"   • Merge strategy: {result.metadata.get('merge_strategy', 'N/A')}")
            
            # Show document relationships if any
            relationships = result.metadata.get('relationships', [])
            if relationships:
                console.print(f"   • Document relationships: {len(relationships)} found")
            
            return result.tree
        else:
            console.print(f"\n[bright_green]✅ Document processing completed for {doc_name}[/bright_green]")
            return result
            
    except Exception as e:
        console.print(f"\n[red]❌ Error processing {doc_name}: {str(e)}[/red]")
        if verbose:
            console.print_exception()
        return None


def save_results(tree_data: dict, output_name: str, output_dir: Path):
    """Save decision tree results."""
    import json
    
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{output_name}_decision_tree.json"
    
    with open(output_file, 'w') as f:
        json.dump(tree_data, f, indent=2)
    
    console.print(f"   💾 Saved to: {output_file}")


@app.command()
def run(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    output_dir: str = typer.Option("outputs/multi_doc", "--output-dir", "-o", help="Output directory"),
    show_trees: bool = typer.Option(True, "--show-trees/--no-trees", help="Display decision trees"),
):
    """
    Run the multi-document demo with Dupixent and Jardiance examples.
    
    Examples:
    - Dupixent: Multi-document (insurance policy + clinical guidelines)
    - Jardiance: Single document (processed through multi-doc pipeline)
    """
    show_multi_doc_banner()
    
    output_path = Path(output_dir)
    
    # Define examples
    examples = [
        {
            "name": "Dupixent (Multi-Document)",
            "files": [
                Path("examples/dupixent_insurance_policy.txt"),
                Path("examples/dupixent_clinical_guidelines.txt")
            ],
            "output_name": "dupixent_multi_doc"
        },
        {
            "name": "Jardiance (Single Document via Multi-Doc Pipeline)",
            "files": [Path("examples/jardiance_criteria.txt")],
            "output_name": "jardiance_single_doc"
        }
    ]
    
    console.print("[bright_blue]🔄 Processing examples through multi-document pipeline...[/bright_blue]\n")
    
    # Process each example
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        console=console,
    ) as progress:
        
        main_task = progress.add_task("Processing documents...", total=len(examples))
        
        for example in examples:
            # Update progress
            progress.update(main_task, description=f"Processing {example['name']}...")
            
            # Check files exist
            missing_files = [f for f in example['files'] if not f.exists()]
            if missing_files:
                console.print(f"[red]❌ Missing files for {example['name']}: {missing_files}[/red]")
                progress.advance(main_task)
                continue
            
            # Process documents
            console.print(f"\n[bright_cyan]📄 {example['name']}[/bright_cyan]")
            for file in example['files']:
                console.print(f"   • {file}")
            
            tree_data = process_documents(example['files'], example['name'], verbose)
            
            if tree_data:
                # Save results
                save_results(tree_data, example['output_name'], output_path)
                
                # Show tree if requested
                if show_trees:
                    presenter.show_decision_tree(tree_data, example['name'], max_depth=10)
            
            progress.advance(main_task)
            time.sleep(0.5)  # Brief pause for visibility
    
    # Summary
    console.print("\n[bright_green]🎉 Multi-document demo completed![/bright_green]")
    console.print(f"\nResults saved to: {output_path}/")
    console.print("\nKey insights:")
    console.print("• Multi-document processing successfully handles both single and multiple documents")
    console.print("• Document relationships are automatically identified through pattern matching")
    console.print("• Supplementary criteria from clinical guidelines are merged with insurance policies")


@app.command()
def list_examples():
    """List the available examples in this demo."""
    console.print("[bright_cyan]📋 Available Examples[/bright_cyan]\n")
    
    examples = [
        {
            "name": "Dupixent (Multi-Document)",
            "files": [
                "examples/dupixent_insurance_policy.txt",
                "examples/dupixent_clinical_guidelines.txt"
            ],
            "description": "Insurance policy + clinical guidelines merged together"
        },
        {
            "name": "Jardiance (Single Document)",
            "files": ["examples/jardiance_criteria.txt"],
            "description": "Single comprehensive criteria document"
        }
    ]
    
    for i, example in enumerate(examples, 1):
        console.print(f"[bold]{i}. {example['name']}[/bold]")
        console.print(f"   [dim]{example['description']}[/dim]")
        for file in example['files']:
            exists = Path(file).exists()
            status = "[green]✓[/green]" if exists else "[red]✗[/red]"
            console.print(f"   {status} {file}")
        console.print()


@app.command()
def info():
    """Show information about multi-document processing."""
    show_multi_doc_banner()
    
    console.print("[bright_cyan]📚 Multi-Document Processing Information[/bright_cyan]\n")
    
    console.print("[bold]How it works:[/bold]")
    console.print("1. Documents are grouped by pattern matching (e.g., dupixent_insurance.txt + dupixent_guidelines.txt)")
    console.print("2. Primary document (insurance policy) forms the base decision tree")
    console.print("3. Supplementary documents (clinical guidelines) add additional criteria")
    console.print("4. Results are merged using configurable strategies\n")
    
    console.print("[bold]Supported patterns:[/bold]")
    console.print("• {drug_name}_{document_type}.txt (e.g., dupixent_insurance.txt)")
    console.print("• {drug_name}-{document_type}.txt (e.g., dupixent-guidelines.txt)")
    console.print("• Manifest files for explicit relationships\n")
    
    console.print("[bold]Current configuration:[/bold]")
    console.print(f"• Multi-document enabled: {os.environ.get('ENABLE_MULTI_DOCUMENT', 'false')}")
    console.print(f"• Merge strategy: {os.environ.get('MULTI_DOC_MERGE_STRATEGY', 'simple_append')}")


@app.command()
def test():
    """Run a quick test to verify multi-document processing works."""
    console.print("[bright_yellow]🧪 Testing multi-document processing components...[/bright_yellow]\n")
    
    try:
        # Test environment variable
        multi_doc_enabled = os.environ.get("ENABLE_MULTI_DOCUMENT", "false")
        console.print(f"✅ Multi-document flag: {multi_doc_enabled}")
        
        # Test document set manager
        from src.utils.document_set_manager import DocumentSetManager
        manager = DocumentSetManager()
        console.print("✅ DocumentSetManager initialized")
        
        # Test with dupixent files
        dupixent_files = [
            Path("examples/dupixent_insurance_policy.txt"),
            Path("examples/dupixent_clinical_guidelines.txt")
        ]
        
        if all(f.exists() for f in dupixent_files):
            doc_set = manager.identify_document_set(dupixent_files)
            if doc_set:
                console.print(f"✅ Document set identified: {doc_set.set_id}")
                console.print(f"   • Primary document: {doc_set.primary_document_id}")
                console.print(f"   • Total documents: {len(doc_set.documents)}")
                console.print(f"   • Relationships: {len(doc_set.relationships)}")
            else:
                console.print("[yellow]⚠️  Could not identify document set[/yellow]")
        else:
            console.print("[yellow]⚠️  Dupixent example files not found[/yellow]")
        
        # Test single file handling
        jardiance_file = Path("examples/jardiance_criteria.txt")
        if jardiance_file.exists():
            single_result = manager.identify_document_set([jardiance_file])
            if single_result is None:
                console.print("✅ Single document correctly returns None (as expected)")
            else:
                console.print("[yellow]⚠️  Single document unexpectedly created a set[/yellow]")
        
        console.print("\n[bright_green]✅ Multi-document components are operational![/bright_green]")
        console.print("\n[dim]Note: Full processing requires GOOGLE_API_KEY environment variable[/dim]")
        
    except Exception as e:
        console.print(f"[red]❌ Test failed: {str(e)}[/red]")
        console.print_exception()


if __name__ == "__main__":
    app()
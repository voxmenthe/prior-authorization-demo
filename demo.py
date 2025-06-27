#!/usr/bin/env python3
"""
Prior Authorization Decision Tree Demo Script

A comprehensive demo script that showcases the entire Prior Authorization
Decision Tree Generation pipeline with rich visual output and multiple
execution modes.
"""

import sys
import time
from pathlib import Path
from typing import Optional, List

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

from src.demo.orchestrator import DemoOrchestrator
from src.demo.presenter import VisualPresenter
from src.demo.tracker import ProgressTracker


# Initialize Rich console and Typer app
console = Console()
presenter = VisualPresenter(console)
app = typer.Typer(
    name="demo",
    help="Prior Authorization Decision Tree Generation Demo",
    rich_markup_mode="rich"
)


@app.command()
def run(
    batch: bool = typer.Option(False, "--batch", help="Run in batch mode without interaction"),
    document: Optional[str] = typer.Option(None, "--document", help="Process specific document only"),
    quick: bool = typer.Option(False, "--quick", help="Quick mode with minimal output"),
    mock: bool = typer.Option(False, "--mock", help="Use mock data instead of real LLM calls"),
    verbose: bool = typer.Option(False, "--verbose", help="Enable verbose logging"),
    output_dir: str = typer.Option("outputs", "--output-dir", help="Output directory path"),
    no_color: bool = typer.Option(False, "--no-color", help="Disable colored output"),
    show_trees: bool = typer.Option(True, "--show-trees/--no-trees", help="Display decision trees"),
    interactive_steps: bool = typer.Option(True, "--interactive-steps/--no-interactive", help="Show step-by-step progress")
):
    """
    Run the Prior Authorization Decision Tree Demo.
    
    This demo processes pharmaceutical criteria documents through the complete
    AI pipeline, generating decision trees with rich visual output.
    """
    
    # Disable colors if requested
    if no_color:
        console._force_terminal = False
    
    # Print banner unless in quick mode
    if not quick:
        presenter.show_banner()
    
    # Initialize components
    try:
        orchestrator = DemoOrchestrator(output_dir=output_dir, verbose=verbose)
        tracker = ProgressTracker()
    except Exception as e:
        presenter.show_error("Failed to initialize demo", str(e))
        sys.exit(1)
    
    # Determine execution mode
    mode = "batch" if batch else "quick" if quick else "interactive"
    if mock:
        mode += "_mock"
    
    # Start session
    session = orchestrator.start_session(mode=mode)
    tracker.start_session()
    
    try:
        if document:
            # Single document mode
            console.print(f"[bright_blue]🔄 Processing single document: {document}[/bright_blue]")
            
            if not Path(document).exists():
                presenter.show_error("Document not found", document)
                sys.exit(1)
            
            # Process single document with enhanced tracking
            doc_metrics = tracker.start_document(Path(document).name)
            result = _process_document_with_tracking(
                orchestrator, tracker, document, 
                interactive_steps and not batch and not quick,
                show_trees and not quick
            )
            tracker.finish_document(result.success, result.error)
            
            if result.success:
                if show_trees:
                    presenter.show_decision_tree(result.decision_tree, result.document_name)
                presenter.show_step_result("Document Processing", True, result.processing_time)
            else:
                presenter.show_step_result("Document Processing", False, result.processing_time, result.error)
        
        else:
            # Multi-document mode
            document_paths = orchestrator.get_example_documents()
            
            if not document_paths:
                presenter.show_error("No example documents found", "Check examples/ directory")
                sys.exit(1)
            
            console.print(f"[bright_blue]🔄 Processing {len(document_paths)} documents...[/bright_blue]")
            
            if not batch and not quick:
                # Interactive mode - ask for confirmation
                if not presenter.prompt_continue("Ready to start processing? Press Enter to continue..."):
                    console.print("[yellow]Demo cancelled by user[/yellow]")
                    sys.exit(0)
            
            # Process documents with enhanced tracking
            results = []
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeElapsedColumn(),
                console=console,
                transient=False
            ) as progress:
                main_task = progress.add_task("Processing documents...", total=len(document_paths))
                
                for i, doc_path in enumerate(document_paths):
                    doc_name = Path(doc_path).name
                    progress.update(main_task, description=f"Processing {doc_name}...")
                    
                    # Track document processing
                    doc_metrics = tracker.start_document(doc_name)
                    result = _process_document_with_tracking(
                        orchestrator, tracker, doc_path,
                        interactive_steps and not batch and not quick,
                        show_trees and not quick
                    )
                    tracker.finish_document(result.success, result.error)
                    results.append(result)
                    
                    # Show result
                    if result.success:
                        presenter.show_step_result(f"{result.document_name}", True, result.processing_time)
                        if show_trees and not quick:
                            presenter.show_decision_tree(result.decision_tree, result.document_name)
                    else:
                        presenter.show_step_result(f"{result.document_name}", False, result.processing_time, result.error)
                    
                    progress.update(main_task, advance=1)
                    
                    # Interactive pause between documents - PAUSE PROGRESS BAR
                    if not batch and not quick and interactive_steps and i < len(document_paths) - 1:
                        # Stop the progress bar to avoid showing misleading percentage
                        progress.stop()
                        
                        # Clear, informative prompt
                        remaining = len(document_paths) - i - 1
                        presenter.prompt_continue(f"\n✅ Document {i+1}/{len(document_paths)} complete! {remaining} remaining documents to process.\n🔄 Press Enter to continue to next document...")
                        
                        # Restart progress bar
                        progress.start()
        
        # Complete session and show comprehensive summary
        completed_session = orchestrator.complete_session()
        
        if not quick:
            presenter.show_rule("Results Summary")
            presenter.show_processing_summary(completed_session)
            
            if verbose:
                presenter.show_session_metrics(completed_session)
        
        presenter.show_completion_message(output_dir)
        
    except KeyboardInterrupt:
        presenter.show_warning("Demo interrupted by user")
        sys.exit(130)
    except Exception as e:
        presenter.show_error("Demo failed", str(e))
        if verbose:
            console.print_exception()
        sys.exit(1)


def _process_document_with_tracking(orchestrator: DemoOrchestrator, tracker: ProgressTracker, 
                                   document_path: str, interactive: bool, show_tree: bool):
    """Process a document with detailed step tracking."""
    steps = ["Criteria Parsing", "Tree Structure", "Validation", "Refinement"]
    
    if interactive:
        for i, step in enumerate(steps):
            presenter.show_pipeline_step(i+1, len(steps), step, Path(document_path).name)
            with tracker.track_step(step):
                time.sleep(0.5)  # Simulate step processing for demo
    
    # Actual document processing
    result = orchestrator.process_document(document_path)
    
    return result


@app.command()
def list_documents():
    """List available example documents."""
    presenter.show_banner()
    
    try:
        orchestrator = DemoOrchestrator()
        documents = orchestrator.get_example_documents()
        
        if not documents:
            presenter.show_error("No example documents found", "Check examples/ directory")
            return
        
        console.print("[bright_blue]📋 Available Documents:[/bright_blue]\n")
        for i, doc_path in enumerate(documents, 1):
            doc_name = Path(doc_path).name
            if Path(doc_path).exists():
                size = Path(doc_path).stat().st_size
                console.print(f"  {i}. [green]{doc_name}[/green] ({size:,} bytes)")
            else:
                console.print(f"  {i}. [red]{doc_name}[/red] (not found)")
    except Exception as e:
        presenter.show_error("Failed to list documents", str(e))


@app.command()
def version():
    """Show version information."""
    console.print("[bright_blue]Prior Authorization Decision Tree Demo v1.0.0[/bright_blue]")
    console.print("[cyan]AI-Powered Clinical Workflow System[/cyan]")


if __name__ == "__main__":
    app()
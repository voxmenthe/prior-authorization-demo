#!/usr/bin/env python3
"""
Enhanced Prior Authorization Decision Tree Demo Script

An improved version of the demo with:
1. Real-time display of agent decision-making process
2. Inline graphical tree visualization using Unicode art
3. Enhanced visual elements and interactive features
"""

import sys
import time
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text
from rich.tree import Tree
from rich.table import Table
from rich.columns import Columns
from rich.align import Align
from rich.rule import Rule

from src.demo.orchestrator import DemoOrchestrator
from src.demo.presenter import VisualPresenter
from src.demo.tracker import ProgressTracker
from src.demo.enhanced_visualizer import (
    RealTimeLayoutManager, 
    UnicodeTreeRenderer, 
    AgentInsightRenderer,
    create_demo_processing_steps
)
from src.utils.tree_traversal import SafeTreeTraverser, TraversalConfig, validate_tree_structure


# Configuration settings
TREE_DISPLAY_MAX_DEPTH = 25  # Maximum depth for decision tree visualization

# Initialize Rich console and Typer app
console = Console()
app = typer.Typer(
    name="enhanced-demo",
    help="Enhanced Prior Authorization Decision Tree Generation Demo",
    rich_markup_mode="rich"
)


class EnhancedVisualPresenter:
    """Enhanced visual presenter with real-time tree building and agent insights."""
    
    def __init__(self, console: Console):
        self.console = console
        self.current_tree_state = {}
        self.agent_insights = []
        self.processing_steps = []
    
    def show_enhanced_banner(self):
        """Show enhanced banner with real-time capabilities."""
        banner_text = Text.assemble(
            ("🧠 ENHANCED DECISION TREE DEMO", "bold bright_blue"),
            ("\n✨ Real-time AI Agent Visualization", "italic cyan"),
            ("\n🌳 Live Tree Building & Agent Insights", "italic green"),
        )
        
        banner_panel = Panel(
            banner_text,
            title="🏥 AI-Powered Healthcare Demo v2.0",
            title_align="center",
            border_style="bright_blue",
            padding=(1, 2)
        )
        
        self.console.print()
        self.console.print(banner_panel)
        self.console.print()
    
    def create_real_time_layout(self) -> Layout:
        """Create layout for real-time display."""
        layout = Layout()
        
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=8)
        )
        
        layout["main"].split_row(
            Layout(name="tree", ratio=2),
            Layout(name="agents", ratio=1)
        )
        
        return layout
    
    def show_agent_thinking(self, agent_name: str, step: str, reasoning: str, confidence: float = 0.8):
        """Display agent reasoning in real-time."""
        thinking_text = Text()
        thinking_text.append(f"🤖 {agent_name}\n", style="bold bright_cyan")
        thinking_text.append(f"Step: {step}\n", style="bright_white")
        thinking_text.append(f"Reasoning: {reasoning}\n", style="dim white")
        
        # Confidence bar
        confidence_bar = "█" * int(confidence * 10) + "░" * (10 - int(confidence * 10))
        thinking_text.append(f"Confidence: {confidence_bar} {confidence*100:.0f}%\n", 
                           style="bright_green" if confidence > 0.7 else "bright_yellow")
        
        panel = Panel(
            thinking_text,
            title=f"🧠 {agent_name} Analysis",
            border_style="cyan",
            padding=(0, 1)
        )
        
        return panel
    
    def create_inline_tree_visual(self, tree_data: Dict[str, Any], highlight_node: str = None) -> Panel:
        """Create inline Unicode tree visualization using enhanced renderer."""
        tree_renderer = UnicodeTreeRenderer()
        tree_visual = tree_renderer.render_tree(tree_data, highlight_node, show_connections=True)
        
        return Panel(
            tree_visual,
            title="🌳 Decision Tree (Real-time)",
            border_style="green",
            padding=(1, 2)
        )
    
    def _build_unicode_tree(self, nodes: Dict[str, Any], highlight_node: str = None) -> Text:
        """Build Unicode art tree visualization."""
        tree_text = Text()
        
        # Handle case where nodes is a JSON string instead of a dict
        if isinstance(nodes, str):
            try:
                import json
                import re
                
                # Clean up common JSON issues from LLM responses
                cleaned_nodes = nodes.strip()
                
                # Remove any control characters that might cause JSON parsing issues
                cleaned_nodes = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', cleaned_nodes)
                
                # Try to fix common escape issues
                cleaned_nodes = cleaned_nodes.replace('\\"', '"').replace("\\'", "'")
                
                parsed_nodes = json.loads(cleaned_nodes)
                if isinstance(parsed_nodes, dict) and 'nodes' in parsed_nodes:
                    nodes = parsed_nodes['nodes']
                else:
                    nodes = parsed_nodes
            except (json.JSONDecodeError, KeyError) as e:
                tree_text.append(f"🚨 Tree data parsing issue detected", style="red")
                tree_text.append(f"\nError: {str(e)}", style="dim red")
                
                # Try to extract error position info for debugging
                error_str = str(e)
                if "char" in error_str and "column" in error_str:
                    import re
                    char_match = re.search(r'char (\d+)', error_str)
                    if char_match:
                        char_pos = int(char_match.group(1))
                        # Show context around the error position
                        start_pos = max(0, char_pos - 50)
                        end_pos = min(len(cleaned_nodes), char_pos + 50)
                        context = cleaned_nodes[start_pos:end_pos]
                        tree_text.append(f"\nData around position {char_pos}: ...{context}...", style="dim yellow")
                
                tree_text.append("\n🌱 This indicates a data serialization issue in the tree generation pipeline.", style="dim yellow")
                tree_text.append("\n📝 Check the refinement agent's data handling for double JSON encoding.", style="dim cyan")
                return tree_text
        
        if not nodes:
            tree_text.append("🌱 No nodes yet...", style="dim italic")
            return tree_text
        
        # Ensure nodes is a dictionary before calling .values()
        if not isinstance(nodes, dict):
            tree_text.append("🚨 Invalid nodes format - expected dictionary", style="red")
            return tree_text
        
        # Validate tree structure before rendering
        is_valid, issues = validate_tree_structure(nodes)
        if not is_valid:
            tree_text.append("⚠️  Tree structure issues detected:\n", style="yellow")
            for issue in issues[:3]:  # Show first 3 issues
                tree_text.append(f"  • {issue}\n", style="dim yellow")
            if len(issues) > 3:
                tree_text.append(f"  • ... and {len(issues) - 3} more issues\n", style="dim yellow")
        
        # Create safe traverser
        config = TraversalConfig(
            max_depth=30,  # Reasonable depth for decision trees
            detect_cycles=True,
            raise_on_cycle=False,
            log_warnings=True
        )
        traverser = SafeTreeTraverser(config)
        
        # Find root nodes
        from src.utils.tree_traversal import find_root_nodes
        root_nodes = find_root_nodes(nodes)
        
        # Use safe traversal for each root
        for i, root in enumerate(root_nodes):
            try:
                # Define processing function
                def process_node(node, context, depth):
                    prefix = context.get('prefix', '')
                    is_last = context.get('is_last', True)
                    self._render_node_safe(tree_text, node, prefix, is_last, highlight_node)
                    return None
                
                # Define children getter
                def get_children(node, all_nodes):
                    children = []
                    connections = node.get("connections", {})
                    
                    if isinstance(connections, dict):
                        child_ids = list(connections.values())
                    else:
                        child_ids = [conn.get("target_node_id") for conn in connections if conn.get("target_node_id")]
                    
                    valid_children = []
                    for child_id in child_ids:
                        if child_id in all_nodes:
                            valid_children.append(all_nodes[child_id])
                    
                    # Create context for each child
                    result = []
                    for idx, child in enumerate(valid_children):
                        is_last_child = idx == len(valid_children) - 1
                        child_prefix = prefix + ("    " if is_last else "│   ")
                        child_context = {
                            'prefix': child_prefix,
                            'is_last': is_last_child
                        }
                        result.append((child, child_context))
                    
                    return result
                
                # Initial context
                initial_context = {'prefix': '', 'is_last': i == len(root_nodes) - 1}
                
                # Perform safe traversal
                traverser.traverse_tree(root, nodes, process_node, get_children, initial_context)
                
                if traverser.has_cycle():
                    tree_text.append("\n⚠️  Circular references were detected and safely handled\n", style="dim yellow")
                    
            except Exception as e:
                tree_text.append(f"\n❌ Error rendering tree: {str(e)}\n", style="red")
        
        return tree_text
    
    def _render_node_safe(self, tree_text: Text, node: Dict[str, Any], prefix: str, is_last: bool, highlight_node: str = None):
        """Safely render a single node without recursion."""
        node_id = node.get("id", "unknown")
        node_type = node.get("type", "unknown")
        
        # Choose connector
        connector = "└── " if is_last else "├── "
        
        # Style based on node type
        if node_type == "question":
            icon = "❓"
            style = "bright_blue"
            text = node.get("question", "Unknown Question")[:50]
        elif node_type == "outcome":
            icon = "🎯"
            style = "bright_green"
            text = node.get("decision", "Unknown Outcome")[:50]
        else:
            icon = "⚪"
            style = "white"
            text = node.get("label", node_id)[:50]
        
        # Highlight if this is the current node being processed
        if highlight_node and node_id == highlight_node:
            style = "bold bright_yellow"
            icon = "🔥"
        
        tree_text.append(f"{prefix}{connector}{icon} ", style="dim white")
        tree_text.append(f"{text}\n", style=style)
    
    def _add_node_to_tree(self, tree_text: Text, node: Dict[str, Any], all_nodes: Dict[str, Any], 
                         prefix: str, is_last: bool, highlight_node: str = None):
        """Legacy method kept for compatibility - redirects to safe traversal."""
        # This method is kept for backward compatibility but now uses safe traversal
        config = TraversalConfig(max_depth=30, detect_cycles=True, raise_on_cycle=False)
        traverser = SafeTreeTraverser(config)
        
        def process_node(n, ctx, depth):
            p = ctx.get('prefix', prefix)
            last = ctx.get('is_last', is_last)
            self._render_node_safe(tree_text, n, p, last, highlight_node)
        
        def get_children(n, all_n):
            children = []
            connections = n.get("connections", {})
            if isinstance(connections, dict):
                child_ids = list(connections.values())
            else:
                child_ids = [conn.get("target_node_id") for conn in connections if conn.get("target_node_id")]
            
            valid_children = [all_n[child_id] for child_id in child_ids if child_id in all_n]
            result = []
            for i, child in enumerate(valid_children):
                is_last_child = i == len(valid_children) - 1
                child_prefix = prefix + ("    " if is_last else "│   ")
                child_context = {'prefix': child_prefix, 'is_last': is_last_child}
                result.append((child, child_context))
            return result
        
        initial_context = {'prefix': prefix, 'is_last': is_last}
        traverser.traverse_tree(node, all_nodes, process_node, get_children, initial_context)
    
    def show_step_insight(self, step_name: str, key_finding: str, impact: str, 
                         data_snippet: str = None) -> Panel:
        """Show insights from processing steps with key findings."""
        insight_text = Text()
        insight_text.append(f"🔍 {step_name}\n\n", style="bold bright_white")
        insight_text.append(f"Key Finding: {key_finding}\n", style="bright_cyan")
        insight_text.append(f"Impact: {impact}\n", style="bright_green")
        
        if data_snippet:
            insight_text.append(f"\nData: {data_snippet[:100]}...", style="dim white")
        
        return Panel(
            insight_text,
            title="💡 Step Insight",
            border_style="bright_magenta",
            padding=(0, 1)
        )
    
    def animate_agent_workflow(self, document_path: str) -> None:
        """Show animated workflow with real-time updates using enhanced visualizer."""
        layout_manager = RealTimeLayoutManager(self.console)
        processing_steps = create_demo_processing_steps()
        
        # Use the enhanced animation system
        layout_manager.animate_processing_sequence(
            Path(document_path).name,
            processing_steps,
            simulate_tree_growth=True
        )
        
        # Final summary
        self.console.print("\n")
        self.console.print(Panel(
            Text("🎉 Decision tree generation completed successfully!", style="bold bright_green"),
            title="✨ Process Complete",
            border_style="bright_green"
        ))
    
    def _simulate_tree_building(self, tree_data: Dict[str, Any], step: int):
        """Simulate progressive tree building."""
        if "nodes" not in tree_data:
            tree_data["nodes"] = {}
        
        # Add nodes progressively based on step
        if step >= 1:
            tree_data["nodes"]["root"] = {
                "id": "root",
                "type": "question",
                "question": "Patient age >= 18 years?",
                "connections": {"true": "diagnosis_check", "false": "deny_age"}
            }
        
        if step >= 2:
            tree_data["nodes"]["diagnosis_check"] = {
                "id": "diagnosis_check", 
                "type": "question",
                "question": "ICD-10 diagnosis confirmed?",
                "connections": {"true": "prior_auth", "false": "deny_diagnosis"}
            }
            tree_data["nodes"]["deny_age"] = {
                "id": "deny_age",
                "type": "outcome", 
                "decision": "DENY: Patient under 18"
            }
        
        if step >= 3:
            tree_data["nodes"]["prior_auth"] = {
                "id": "prior_auth",
                "type": "question",
                "question": "Prior authorization required?", 
                "connections": {"true": "submit_auth", "false": "approve"}
            }
            tree_data["nodes"]["deny_diagnosis"] = {
                "id": "deny_diagnosis",
                "type": "outcome",
                "decision": "DENY: Diagnosis not confirmed"
            }
        
        if step >= 4:
            tree_data["nodes"]["submit_auth"] = {
                "id": "submit_auth",
                "type": "outcome",
                "decision": "APPROVE: Submit for authorization"
            }
            tree_data["nodes"]["approve"] = {
                "id": "approve", 
                "type": "outcome",
                "decision": "APPROVE: No prior auth needed"
            }


@app.command()
def run(
    batch: bool = typer.Option(False, "--batch", help="Run in batch mode without interaction"),
    document: Optional[str] = typer.Option(None, "--document", help="Process specific document only"),
    quick: bool = typer.Option(False, "--quick", help="Quick mode with minimal output"),
    mock: bool = typer.Option(False, "--mock", help="Use mock data instead of real LLM calls"),
    verbose: bool = typer.Option(False, "--verbose", help="Enable verbose logging"),
    output_dir: str = typer.Option("outputs", "--output-dir", help="Output directory path"),
    no_color: bool = typer.Option(False, "--no-color", help="Disable colored output"),
    real_time: bool = typer.Option(True, "--real-time/--no-real-time", help="Show real-time agent visualization"),
    animated: bool = typer.Option(True, "--animated/--static", help="Use animated displays")
):
    """
    Run the Enhanced Prior Authorization Decision Tree Demo.
    
    Features real-time agent visualization, inline tree graphics, and enhanced UX.
    """
    
    # Disable colors if requested
    if no_color:
        console._force_terminal = False
    
    # Initialize enhanced presenter
    enhanced_presenter = EnhancedVisualPresenter(console)
    
    # Show enhanced banner unless in quick mode
    if not quick:
        enhanced_presenter.show_enhanced_banner()
    
    # Initialize components
    try:
        orchestrator = DemoOrchestrator(output_dir=output_dir, verbose=verbose)
        tracker = ProgressTracker()
        presenter = VisualPresenter(console)  # Keep original for compatibility
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
            # Single document mode with enhanced visualization
            console.print(f"[bright_blue]🔄 Processing document with enhanced visualization: {document}[/bright_blue]")
            
            if not Path(document).exists():
                presenter.show_error("Document not found", document)
                sys.exit(1)
            
            # Show animated workflow if enabled
            if animated and real_time and not batch and not quick:
                enhanced_presenter.animate_agent_workflow(document)
            
            # Process document with enhanced tracking
            doc_metrics = tracker.start_document(Path(document).name)
            result = _process_document_with_enhanced_tracking(
                orchestrator, tracker, enhanced_presenter, document,
                real_time and not batch and not quick,
                animated and not quick
            )
            tracker.finish_document(result.success, result.error)
            
            # IMPORTANT: Add result to session manually since we're not using process_multiple_documents
            if orchestrator.session:
                orchestrator.session.document_results.append(result)
                orchestrator.session.total_documents = 1
                if result.success:
                    orchestrator.session.successful_documents += 1
                else:
                    orchestrator.session.failed_documents += 1
                orchestrator.session.total_processing_time += result.processing_time
                orchestrator.session.total_api_calls += result.api_calls
                orchestrator.session.total_tokens += result.tokens_used
            
            if result.success:
                # Show enhanced tree visualization
                if real_time:
                    tree_panel = enhanced_presenter.create_inline_tree_visual(result.decision_tree)
                    console.print(tree_panel)
                else:
                    presenter.show_decision_tree(result.decision_tree, result.document_name)
                presenter.show_step_result("Document Processing", True, result.processing_time)
            else:
                presenter.show_step_result("Document Processing", False, result.processing_time, result.error)
        
        else:
            # Multi-document mode with enhanced features
            document_paths = orchestrator.get_example_documents()
            
            if not document_paths:
                presenter.show_error("No example documents found", "Check examples/ directory")
                sys.exit(1)
            
            console.print(f"[bright_blue]🔄 Processing {len(document_paths)} documents with enhanced visualization...[/bright_blue]")
            
            if not batch and not quick:
                if not presenter.prompt_continue("Ready to start enhanced processing? Press Enter to continue..."):
                    console.print("[yellow]Demo cancelled by user[/yellow]")
                    sys.exit(0)
            
            # Process documents with enhanced visualization - Set total documents first
            orchestrator.session.total_documents = len(document_paths)
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
                    progress.update(main_task, description=f"🧠 Processing {doc_name}...")
                    
                    # Show animated workflow for each document if enabled
                    if animated and real_time and not batch and not quick:
                        progress.stop()
                        enhanced_presenter.animate_agent_workflow(doc_path)
                        progress.start()
                    
                    # Track document processing
                    doc_metrics = tracker.start_document(doc_name)
                    result = _process_document_with_enhanced_tracking(
                        orchestrator, tracker, enhanced_presenter, doc_path,
                        real_time and not batch and not quick,
                        animated and not quick
                    )
                    tracker.finish_document(result.success, result.error)
                    results.append(result)
                    
                    # Add result to orchestrator session for proper summary display
                    orchestrator.session.document_results.append(result)
                    
                    # Update session metrics
                    if result.success:
                        orchestrator.session.successful_documents += 1
                    else:
                        orchestrator.session.failed_documents += 1
                        
                    orchestrator.session.total_processing_time += result.processing_time
                    orchestrator.session.total_api_calls += result.api_calls
                    orchestrator.session.total_tokens += result.tokens_used
                    
                    # Show enhanced result
                    if result.success:
                        presenter.show_step_result(f"✨ {result.document_name}", True, result.processing_time)
                        if real_time and not quick:
                            tree_panel = enhanced_presenter.create_inline_tree_visual(result.decision_tree)
                            console.print(tree_panel)
                    else:
                        presenter.show_step_result(f"❌ {result.document_name}", False, result.processing_time, result.error)
                    
                    progress.update(main_task, advance=1)
                    
                    # Enhanced interactive pause
                    if not batch and not quick and real_time and i < len(document_paths) - 1:
                        progress.stop()
                        remaining = len(document_paths) - i - 1
                        presenter.prompt_continue(
                            f"\n🎉 Document {i+1}/{len(document_paths)} completed with enhanced visualization! "
                            f"{remaining} remaining.\n✨ Press Enter to continue..."
                        )
                        progress.start()
        
        # Complete session and show enhanced summary
        completed_session = orchestrator.complete_session()
        
        if not quick:
            presenter.show_rule("🌟 Enhanced Results Summary")
            presenter.show_processing_summary(completed_session)
            
            if verbose:
                presenter.show_session_metrics(completed_session)
        
        # Enhanced completion message with specific filenames
        output_path = Path(output_dir)
        
        # Get actual output files
        decision_tree_files = list((output_path / "decision_trees").glob("*.json")) if (output_path / "decision_trees").exists() else []
        report_files = list((output_path / "reports").glob("*.json")) if (output_path / "reports").exists() else []
        log_files = list((output_path / "logs").glob("*.log")) if (output_path / "logs").exists() else []
        
        completion_text = Text.assemble(
            ("🎉 Enhanced Demo Completed Successfully!", "bold bright_green"),
            (f"\n\n✨ Features used:", "bright_cyan"),
            (f"\n• Real-time agent visualization: {'✅' if real_time else '❌'}", "white"),
            (f"\n• Animated tree building: {'✅' if animated else '❌'}", "white"),
            (f"\n\n📁 Output saved to: {output_dir}/", "bright_blue"),
        )
        
        # Add decision tree files
        if decision_tree_files:
            completion_text.append("\n\n🌳 Decision trees:", "bright_magenta")
            for file in decision_tree_files:
                completion_text.append(f"\n  • {file.name}", "dim white")
        
        # Add report files
        if report_files:
            completion_text.append("\n\n📊 Session reports:", "bright_magenta")
            for file in report_files:
                completion_text.append(f"\n  • {file.name}", "dim white")
        
        # Add log files
        if log_files:
            completion_text.append("\n\n📝 Detailed logs:", "bright_magenta")
            for file in log_files:
                completion_text.append(f"\n  • {file.name}", "dim white")
        
        completion_panel = Panel(
            completion_text,
            title="🌟 Enhanced Demo Complete",
            title_align="center",
            border_style="bright_green",
            padding=(1, 2)
        )
        
        console.print()
        console.print(completion_panel)
        
    except KeyboardInterrupt:
        presenter.show_warning("Enhanced demo interrupted by user")
        sys.exit(130)
    except Exception as e:
        presenter.show_error("Enhanced demo failed", str(e))
        if verbose:
            console.print_exception()
        sys.exit(1)


def _process_document_with_enhanced_tracking(orchestrator: DemoOrchestrator, tracker: ProgressTracker,
                                           enhanced_presenter: EnhancedVisualPresenter, document_path: str,
                                           real_time: bool, animated: bool):
    """Process a document with enhanced step tracking and visualization."""
    steps = ["Criteria Parsing", "Tree Structure", "Validation", "Refinement"]
    
    if real_time and not animated:  # If not using full animation, show step-by-step insights
        for i, step in enumerate(steps):
            enhanced_presenter.console.print(f"\n🔄 {step}...")
            
            # Show step insights
            insights = {
                "Criteria Parsing": ("Extracting eligibility rules", "Found key decision points"),
                "Tree Structure": ("Building decision nodes", "Created logical pathways"),
                "Validation": ("Checking completeness", "Validated all branches"),
                "Refinement": ("Optimizing structure", "Enhanced readability")
            }
            
            finding, impact = insights.get(step, ("Processing...", "Analyzing data"))
            insight_panel = enhanced_presenter.show_step_insight(step, finding, impact)
            enhanced_presenter.console.print(insight_panel)
            
            with tracker.track_step(step):
                time.sleep(1.0)  # Simulate processing time
    
    # Actual document processing
    result = orchestrator.process_document(document_path)
    
    return result


@app.command()
def demo_features():
    """Demonstrate the enhanced features of this demo."""
    enhanced_presenter = EnhancedVisualPresenter(console)
    enhanced_presenter.show_enhanced_banner()
    
    console.print("[bright_cyan]🌟 Enhanced Demo Features:[/bright_cyan]\n")
    
    features = [
        ("🧠 Real-time Agent Visualization", "Watch AI agents think and reason through each step"),
        ("🌳 Live Tree Building", "See decision trees grow in real-time with Unicode art"),
        ("💡 Step Insights", "Get detailed explanations of what each agent discovers"),
        ("🎨 Enhanced UI/UX", "Beautiful, interactive terminal experience"),
        ("⚡ Confidence Indicators", "Visual confidence bars for AI decisions"),
        ("🔥 Active Node Highlighting", "See which part of the tree is being processed"),
        ("📊 Progressive Visualization", "Trees build progressively as agents work"),
        ("✨ Animated Workflows", "Smooth animations showing the complete process")
    ]
    
    for feature, description in features:
        console.print(f"  {feature}")
        console.print(f"    [dim]{description}[/dim]\n")
    
    console.print("[bright_green]🚀 Try: `python enhanced_demo.py run --real-time --animated`[/bright_green]")


@app.command()
def version():
    """Show enhanced demo version information."""
    console.print("[bright_blue]Enhanced Prior Authorization Decision Tree Demo v2.0[/bright_blue]")
    console.print("[cyan]🧠 AI-Powered Clinical Workflow with Real-time Visualization[/cyan]")
    console.print("[dim]✨ Features: Live agent insights, animated tree building, enhanced UX[/dim]")


if __name__ == "__main__":
    app()
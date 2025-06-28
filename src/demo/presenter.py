"""
Visual Presenter - Rich console output management.

This module handles all rich formatting, progress displays, tree visualization,
and interactive elements for the demo script.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.tree import Tree
from rich.columns import Columns
from rich.align import Align
from rich.rule import Rule
from rich.layout import Layout
from rich.live import Live

from src.demo.orchestrator import DocumentResult, DemoSession


class Colors:
    """Centralized color scheme for consistent visual identity."""
    
    # Primary colors
    PRIMARY = "bright_blue"
    SUCCESS = "bright_green"
    WARNING = "bright_yellow"
    ERROR = "bright_red"
    INFO = "cyan"
    ACCENT = "magenta"
    MUTED = "dim white"
    
    # Semantic colors
    PROCESSING = "bright_blue"
    COMPLETED = "bright_green"
    FAILED = "bright_red"
    SKIPPED = "bright_yellow"
    
    # UI elements
    BORDER = "bright_blue"
    TITLE = "bold bright_blue"
    SUBTITLE = "italic cyan"
    HIGHLIGHT = "bold bright_white"


class VisualPresenter:
    """
    Rich console output management for the demo.
    
    Provides comprehensive visual formatting including progress bars,
    status updates, decision tree visualization, and summary tables.
    """
    
    def __init__(self, console: Optional[Console] = None):
        """
        Initialize the visual presenter.
        
        Args:
            console: Optional Rich console instance. Creates new one if None.
        """
        self.console = console or Console()
        self.colors = Colors()
    
    def show_banner(self) -> None:
        """Display the main demo banner."""
        banner_text = Text.assemble(
            ("PRIOR AUTHORIZATION", f"bold {self.colors.PRIMARY}"),
            ("\nDECISION TREE DEMO", f"bold {self.colors.PRIMARY}"),
            ("\n\nAI-Powered Clinical Workflow", f"italic {self.colors.SUBTITLE}"),
        )
        
        banner_panel = Panel(
            banner_text,
            title="🏥 Healthcare AI Demo",
            title_align="center",
            border_style=self.colors.BORDER,
            padding=(1, 2)
        )
        
        self.console.print()
        self.console.print(banner_panel)
        self.console.print()
    
    def show_pipeline_step(self, step_number: int, total_steps: int, 
                          step_name: str, document_name: str = None) -> None:
        """Display pipeline step header."""
        step_text = f"🔄 PIPELINE STEP {step_number}/{total_steps}: {step_name}"
        
        if document_name:
            subtitle = f"Document: {document_name}"
        else:
            subtitle = None
        
        panel = Panel(
            Text(step_text, style=f"bold {self.colors.PROCESSING}"),
            subtitle=subtitle,
            border_style=self.colors.BORDER,
            padding=(0, 1)
        )
        
        self.console.print(panel)
    
    def show_document_processing(self, document_name: str, 
                               processing_steps: List[str]) -> Progress:
        """
        Show document processing with detailed steps.
        
        Args:
            document_name: Name of document being processed
            processing_steps: List of processing step names
            
        Returns:
            Progress object for updating steps
        """
        self.console.print(f"\n[{self.colors.INFO}]📄 Processing: {document_name}[/{self.colors.INFO}]")
        
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=self.console,
            transient=False
        )
        
        return progress
    
    def show_step_result(self, step_name: str, success: bool, 
                        duration: float = None, details: str = None) -> None:
        """Show result of a processing step."""
        if success:
            icon = "✅"
            color = self.colors.SUCCESS
            status = "Success"
        else:
            icon = "❌"
            color = self.colors.ERROR
            status = "Failed"
        
        result_text = f"{icon} {step_name}: {status}"
        
        if duration:
            result_text += f" ({duration:.1f}s)"
        
        if details:
            result_text += f" - {details}"
        
        self.console.print(f"[{color}]{result_text}[/{color}]")
    
    def show_decision_tree(self, tree_data: Dict[str, Any], 
                          document_name: str, max_depth: int = 15) -> None:
        """
        Display decision tree in ASCII art format.
        
        Args:
            tree_data: Decision tree data structure
            document_name: Name of source document
            max_depth: Maximum depth to display (default: 15)
        """
        # Extract medication name from document name
        medication = document_name.replace("_criteria.txt", "").replace(".txt", "").title()
        
        tree_title = f"📊 GENERATED DECISION TREE: {medication}"
        
        # Create Rich Tree visualization
        tree = Tree(
            f"[bold {self.colors.PRIMARY}]Root: Patient Eligibility[/bold {self.colors.PRIMARY}]",
            guide_style=self.colors.MUTED
        )
        
        # Check if tree_data has nodes and handle both dict and list formats
        if tree_data and "nodes" in tree_data:
            nodes = tree_data["nodes"]
            
            # If nodes is a dictionary (node_id -> node_data), convert to list and build tree
            if isinstance(nodes, dict):
                # Get start node if available
                start_node_id = tree_data.get("start_node")
                if start_node_id and start_node_id in nodes:
                    # Build tree starting from start_node
                    self._build_tree_from_dict(tree, nodes, start_node_id, visited=set(), max_depth=max_depth)
                else:
                    # Convert dict to list and build
                    nodes_list = list(nodes.values())
                    self._build_tree_nodes(tree, nodes_list)
            else:
                # nodes is already a list
                self._build_tree_nodes(tree, nodes)
        else:
            # Fallback generic structure
            age_branch = tree.add(f"[{self.colors.INFO}]Age >= 18?[/{self.colors.INFO}]")
            age_branch.add(f"[{self.colors.SUCCESS}][Yes] → Diagnosis Check[/{self.colors.SUCCESS}]")
            age_branch.add(f"[{self.colors.ERROR}][No] → DENY: Under 18[/{self.colors.ERROR}]")
            
            dx_branch = tree.add(f"[{self.colors.INFO}]Diagnosis Confirmed?[/{self.colors.INFO}]")
            dx_branch.add(f"[{self.colors.SUCCESS}][Yes] → APPROVE[/{self.colors.SUCCESS}]")
            dx_branch.add(f"[{self.colors.WARNING}][No] → Additional Review[/{self.colors.WARNING}]")
        
        tree_panel = Panel(
            tree,
            title=tree_title,
            title_align="center",
            border_style=self.colors.BORDER,
            padding=(1, 2)
        )
        
        self.console.print(tree_panel)
    
    def _build_tree_from_dict(self, parent_tree: Tree, nodes: Dict[str, Any], 
                              node_id: str, visited: set, depth: int = 0, max_depth: int = 15) -> None:
        """Build tree recursively from dict format nodes."""
        if node_id in visited or depth > max_depth:  # Prevent infinite loops
            return
        
        visited.add(node_id)
        
        if node_id not in nodes:
            return
        
        node = nodes[node_id]
        
        # Determine node text and color
        if node.get("type") == "outcome":
            decision = node.get("decision", "UNKNOWN")
            message = node.get("message", decision)
            if decision == "APPROVED":
                color = self.colors.SUCCESS
                icon = "✅"
            elif decision == "DENIED":
                color = self.colors.ERROR
                icon = "❌"
            else:
                color = self.colors.WARNING
                icon = "⚠️"
            node_text = f"{icon} {message[:80]}..." if len(message) > 80 else f"{icon} {message}"
        else:
            # Regular question node
            question = node.get("question", node.get("condition", f"Node {node_id}"))
            node_text = question
            color = self.colors.INFO
        
        # Add this node to the tree
        branch = parent_tree.add(f"[{color}]{node_text}[/{color}]")
        
        # Add connections if they exist
        connections = node.get("connections", {})
        if connections:
            # Handle different connection formats
            if isinstance(connections, dict):
                # Format: {"yes": "next_node", "no": "other_node"}
                for condition, target_id in connections.items():
                    if target_id and target_id in nodes:
                        target_node = nodes[target_id]
                        target_type = target_node.get("type", "")
                        
                        # Create sub-branch label with better formatting
                        if target_type == "outcome":
                            decision = target_node.get("decision", "Unknown")
                            if decision == "APPROVED":
                                target_label = f"[{condition}] → ✅ APPROVED"
                            elif decision == "DENIED":
                                target_label = f"[{condition}] → ❌ DENIED"
                            else:
                                target_label = f"[{condition}] → {decision}"
                        else:
                            # Show a preview of the next question
                            next_question = target_node.get("question", "Next Question")
                            if len(next_question) > 40:
                                next_question = next_question[:40] + "..."
                            target_label = f"[{condition}] → {next_question}"
                        
                        sub_branch = branch.add(f"[{self.colors.MUTED}]{target_label}[/{self.colors.MUTED}]")
                        
                        # Recursively build the subtree (but not for outcomes)
                        if target_type != "outcome":
                            self._build_tree_from_dict(sub_branch, nodes, target_id, visited, depth + 1, max_depth)
            elif isinstance(connections, list):
                # Format: [{"condition": "...", "target": "..."}]
                for conn in connections:
                    if isinstance(conn, dict):
                        condition = conn.get("condition", "Condition")
                        target_id = conn.get("target", conn.get("target_node_id"))
                        if target_id:
                            sub_branch = branch.add(f"[{self.colors.MUTED}][{condition}] → {target_id}[/{self.colors.MUTED}]")

    def _build_tree_nodes(self, tree: Tree, nodes: List[Dict[str, Any]]) -> None:
        """Helper method to build tree nodes from decision tree data."""
        for i, node in enumerate(nodes):
            if isinstance(node, dict):
                # Get node text based on type
                node_type = node.get("type", "unknown")
                
                if node_type == "outcome":
                    decision = node.get("decision", "Unknown")
                    message = node.get("message", decision)
                    if decision == "APPROVED":
                        color = self.colors.SUCCESS
                        icon = "✅"
                    elif decision == "DENIED":
                        color = self.colors.ERROR
                        icon = "❌"
                    else:
                        color = self.colors.WARNING
                        icon = "⚠️"
                    node_text = f"{icon} {message[:60]}..." if len(message) > 60 else f"{icon} {message}"
                else:
                    # Regular question node
                    node_text = node.get("question", node.get("condition", f"Decision Point {i+1}"))
                    color = self.colors.INFO
                
                branch = tree.add(f"[{color}]{node_text}[/{color}]")
                
                # Add connections
                connections = node.get("connections", {})
                if isinstance(connections, dict):
                    # Dict format: {"yes": "target_id", "no": "target_id"}
                    for condition, target in connections.items():
                        branch.add(f"[{self.colors.MUTED}][{condition}] → {target}[/{self.colors.MUTED}]")
                elif isinstance(connections, list):
                    # List format: [{"condition": "...", "target_node_id": "..."}]
                    for conn in connections[:2]:  # Limit to avoid clutter
                        if isinstance(conn, dict):
                            condition = conn.get("condition", "Option")
                            target = conn.get("target_node_id", conn.get("target", "Next"))
                            branch.add(f"[{self.colors.MUTED}][{condition}] → {target}[/{self.colors.MUTED}]")
    
    def show_processing_summary(self, session: DemoSession) -> None:
        """Display comprehensive processing summary."""
        if not session.document_results:
            self.console.print(f"[{self.colors.WARNING}]⚠️ No processing results available[/{self.colors.WARNING}]")
            return
        
        # Create summary table
        table = Table(
            title="📈 PROCESSING SUMMARY",
            border_style=self.colors.BORDER,
            title_style=f"bold {self.colors.TITLE}"
        )
        
        table.add_column("Document", style=self.colors.INFO, no_wrap=True)
        table.add_column("Status", justify="center")
        table.add_column("Time", justify="right", style=self.colors.ACCENT)
        table.add_column("Result", style=self.colors.MUTED)
        
        for result in session.document_results:
            # Status with colored icon
            if result.success:
                status = f"[{self.colors.SUCCESS}]✅ Success[/{self.colors.SUCCESS}]"
                result_text = "Decision Tree Generated"
            else:
                status = f"[{self.colors.ERROR}]❌ Failed[/{self.colors.ERROR}]"
                result_text = result.error[:50] + "..." if result.error and len(result.error) > 50 else result.error or "Unknown error"
            
            table.add_row(
                result.document_name.replace("_criteria.txt", ""),
                status,
                f"{result.processing_time:.1f}s",
                result_text
            )
        
        # Add totals row
        total_time = sum(r.processing_time for r in session.document_results)
        success_count = sum(1 for r in session.document_results if r.success)
        
        table.add_section()
        table.add_row(
            f"[bold]TOTAL ({len(session.document_results)} documents)[/bold]",
            f"[bold]{success_count}/{len(session.document_results)}[/bold]",
            f"[bold]{total_time:.1f}s[/bold]",
            f"[bold]Avg: {total_time/len(session.document_results):.1f}s[/bold]"
        )
        
        self.console.print(table)
    
    def show_session_metrics(self, session: DemoSession) -> None:
        """Display detailed session metrics."""
        if not session.completed_at:
            return
        
        duration = (session.completed_at - session.started_at).total_seconds()
        
        metrics_text = Text()
        metrics_text.append("📊 Session Metrics\n\n", style=f"bold {self.colors.TITLE}")
        metrics_text.append(f"Duration: {duration:.1f}s\n", style=self.colors.INFO)
        metrics_text.append(f"Mode: {session.mode}\n", style=self.colors.INFO)
        metrics_text.append(f"Success Rate: {session.successful_documents}/{session.total_documents}", style=self.colors.SUCCESS)
        
        if session.total_api_calls > 0:
            metrics_text.append(f"\nAPI Calls: {session.total_api_calls}", style=self.colors.ACCENT)
        if session.total_tokens > 0:
            metrics_text.append(f"\nTokens: {session.total_tokens:,}", style=self.colors.ACCENT)
        
        metrics_panel = Panel(
            metrics_text,
            border_style=self.colors.BORDER,
            padding=(1, 2)
        )
        
        self.console.print(metrics_panel)
    
    def show_error(self, message: str, details: str = None) -> None:
        """Display error message with optional details."""
        error_text = Text()
        error_text.append("❌ ERROR: ", style=f"bold {self.colors.ERROR}")
        error_text.append(message, style=self.colors.ERROR)
        
        if details:
            error_text.append(f"\nDetails: {details}", style=self.colors.MUTED)
        
        error_panel = Panel(
            error_text,
            title="Error",
            title_align="center",
            border_style=self.colors.ERROR,
            padding=(1, 2)
        )
        
        self.console.print(error_panel)
    
    def show_warning(self, message: str, details: str = None) -> None:
        """Display warning message with optional details."""
        warning_text = Text()
        warning_text.append("⚠️ WARNING: ", style=f"bold {self.colors.WARNING}")
        warning_text.append(message, style=self.colors.WARNING)
        
        if details:
            warning_text.append(f"\nDetails: {details}", style=self.colors.MUTED)
        
        warning_panel = Panel(
            warning_text,
            title="Warning",
            title_align="center",
            border_style=self.colors.WARNING,
            padding=(1, 2)
        )
        
        self.console.print(warning_panel)
    
    def show_completion_message(self, output_dir: str) -> None:
        """Display demo completion message with specific filenames."""
        output_path = Path(output_dir)
        
        # Get actual output files
        decision_tree_files = list((output_path / "decision_trees").glob("*.json")) if (output_path / "decision_trees").exists() else []
        report_files = list((output_path / "reports").glob("*.json")) if (output_path / "reports").exists() else []
        log_files = list((output_path / "logs").glob("*.log")) if (output_path / "logs").exists() else []
        
        completion_text = Text.assemble(
            ("🎉 Demo Completed Successfully!", f"bold {self.colors.SUCCESS}"),
            (f"\n\n📁 Output saved to: {output_dir}/", self.colors.INFO),
        )
        
        # Add decision tree files
        if decision_tree_files:
            completion_text.append("\n\n🌳 Decision trees:", self.colors.ACCENT)
            for file in decision_tree_files:
                completion_text.append(f"\n  • {file.name}", self.colors.MUTED)
        
        # Add report files
        if report_files:
            completion_text.append("\n\n📊 Session reports:", self.colors.ACCENT)
            for file in report_files:
                completion_text.append(f"\n  • {file.name}", self.colors.MUTED)
        
        # Add log files
        if log_files:
            completion_text.append("\n\n📝 Detailed logs:", self.colors.ACCENT)
            for file in log_files:
                completion_text.append(f"\n  • {file.name}", self.colors.MUTED)
        
        # If no specific files found, show generic folder structure
        if not decision_tree_files and not report_files and not log_files:
            completion_text.append("\n• Decision trees: decision_trees/", self.colors.MUTED)
            completion_text.append("\n• Session reports: reports/", self.colors.MUTED)
            completion_text.append("\n• Detailed logs: logs/", self.colors.MUTED)
        
        completion_panel = Panel(
            completion_text,
            title="✨ Success",
            title_align="center",
            border_style=self.colors.SUCCESS,
            padding=(1, 2)
        )
        
        self.console.print()
        self.console.print(completion_panel)
    
    def prompt_continue(self, message: str = "Press Enter to continue...") -> bool:
        """Show interactive prompt to continue."""
        try:
            self.console.print(f"\n[{self.colors.ACCENT}]{message}[/{self.colors.ACCENT}]", end="")
            input()
            return True
        except KeyboardInterrupt:
            self.console.print(f"\n[{self.colors.WARNING}]⚠️ Interrupted by user[/{self.colors.WARNING}]")
            return False
    
    def show_rule(self, title: str = None) -> None:
        """Show a horizontal rule separator."""
        rule = Rule(title=title, style=self.colors.BORDER)
        self.console.print(rule)
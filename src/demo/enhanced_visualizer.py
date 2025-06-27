"""
Enhanced Visualization Module

Provides advanced visualization capabilities for the enhanced demo including:
- Real-time Unicode tree rendering
- Agent insight displays  
- Animated progress indicators
- Interactive terminal layouts
"""

import time
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree
from rich.layout import Layout
from rich.live import Live
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.columns import Columns
from rich.align import Align


class TreeNodeStyle:
    """Styling constants for different node types."""
    
    QUESTION = {
        'icon': '❓',
        'style': 'bright_blue',
        'border': 'blue'
    }
    
    OUTCOME = {
        'icon': '🎯', 
        'style': 'bright_green',
        'border': 'green'
    }
    
    PROCESSING = {
        'icon': '🔥',
        'style': 'bold bright_yellow',
        'border': 'yellow'
    }
    
    DEFAULT = {
        'icon': '⚪',
        'style': 'white',
        'border': 'white'
    }


class AgentInsightRenderer:
    """Renders agent thinking and reasoning processes."""
    
    def __init__(self, console: Console):
        self.console = console
        
    def create_thinking_panel(self, agent_name: str, current_step: str, 
                            reasoning: str, confidence: float = 0.8,
                            data_points: List[str] = None) -> Panel:
        """Create a panel showing agent's current thinking process."""
        
        # Agent header with icon
        agent_icons = {
            'CriteriaParser': '📋',
            'TreeStructure': '🌳', 
            'Validation': '✅',
            'Refinement': '⚡'
        }
        
        icon = agent_icons.get(agent_name, '🤖')
        
        thinking_text = Text()
        thinking_text.append(f"{icon} {agent_name}\n", style="bold bright_cyan")
        thinking_text.append(f"Current Step: {current_step}\n\n", style="bright_white")
        
        # Reasoning section
        thinking_text.append("🧠 Reasoning:\n", style="bold bright_magenta")
        thinking_text.append(f"{reasoning}\n\n", style="white")
        
        # Confidence visualization
        thinking_text.append("📊 Confidence: ", style="bold")
        confidence_bar = self._create_confidence_bar(confidence)
        thinking_text.append(confidence_bar)
        thinking_text.append(f" {confidence*100:.0f}%\n\n", style="bright_white")
        
        # Data points if provided
        if data_points:
            thinking_text.append("📌 Key Data Points:\n", style="bold bright_green")
            for point in data_points[:3]:  # Limit to 3 points for readability
                thinking_text.append(f"• {point}\n", style="dim white")
        
        return Panel(
            thinking_text,
            title=f"🧠 {agent_name} Analysis",
            border_style="cyan",
            padding=(1, 1)
        )
    
    def _create_confidence_bar(self, confidence: float) -> str:
        """Create a visual confidence bar."""
        filled = int(confidence * 10)
        empty = 10 - filled
        
        if confidence >= 0.8:
            bar_style = "bright_green"
        elif confidence >= 0.6:
            bar_style = "bright_yellow"
        else:
            bar_style = "bright_red"
            
        return f"[{bar_style}]{'█' * filled}{'░' * empty}[/{bar_style}]"
    
    def create_step_insight_panel(self, step_name: str, findings: Dict[str, Any],
                                 processing_time: float = None) -> Panel:
        """Create insight panel for processing step results."""
        
        insight_text = Text()
        insight_text.append(f"💡 {step_name} Insights\n\n", style="bold bright_white")
        
        # Key findings
        if 'key_finding' in findings:
            insight_text.append("🔍 Key Finding:\n", style="bold bright_cyan")
            insight_text.append(f"{findings['key_finding']}\n\n", style="white")
        
        if 'impact' in findings:
            insight_text.append("⚡ Impact:\n", style="bold bright_green") 
            insight_text.append(f"{findings['impact']}\n\n", style="white")
        
        if 'metrics' in findings:
            insight_text.append("📈 Metrics:\n", style="bold bright_magenta")
            for key, value in findings['metrics'].items():
                insight_text.append(f"• {key}: {value}\n", style="dim white")
            insight_text.append("\n")
        
        # Processing time
        if processing_time:
            insight_text.append(f"⏱️ Processing Time: {processing_time:.2f}s", style="dim bright_blue")
        
        return Panel(
            insight_text,
            title="💡 Step Analysis",
            border_style="bright_magenta",
            padding=(1, 1)
        )


class UnicodeTreeRenderer:
    """Renders decision trees using Unicode art."""
    
    def __init__(self):
        self.node_styles = TreeNodeStyle()
    
    def render_tree(self, tree_data: Dict[str, Any], 
                   highlight_node: str = None,
                   show_connections: bool = True) -> Text:
        """Render complete tree structure with Unicode art."""
        
        if not tree_data or 'nodes' not in tree_data:
            return Text("🌱 Tree is being constructed...", style="dim italic")
        
        nodes = tree_data['nodes']
        
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
                # Fallback: show detailed error information
                error_text = Text()
                error_text.append("🚨 Tree data parsing issue detected\n", style="red")
                error_text.append(f"Error: {str(e)}\n", style="dim red")
                
                # Show snippet of the problematic data for debugging
                if hasattr(e, 'pos') and isinstance(nodes, str):
                    pos = e.pos
                    start = max(0, pos - 50)
                    end = min(len(nodes), pos + 50)
                    snippet = nodes[start:end]
                    error_text.append(f"Data around position {pos}: ...{snippet}...\n", style="dim yellow")
                
                error_text.append("🌱 This indicates a data serialization issue in the tree generation pipeline.\n", style="yellow")
                error_text.append("📝 Check the refinement agent's data handling for double JSON encoding.\n", style="cyan")
                return error_text
        
        if not nodes:
            return Text("🌱 No nodes available yet...", style="dim italic")
        
        # Ensure nodes is a dictionary before processing
        if not isinstance(nodes, dict):
            error_text = Text()
            error_text.append("🚨 Invalid nodes format - expected dictionary\n", style="red")
            error_text.append(f"Received: {type(nodes).__name__}", style="dim red")
            return error_text
        
        # Find root nodes (nodes with no incoming connections)
        root_nodes = self._find_root_nodes(nodes)
        
        tree_text = Text()
        
        # Add tree header
        tree_text.append("🌳 Decision Tree Structure\n\n", style="bold bright_green")
        
        # Render each root node and its subtree
        for i, root in enumerate(root_nodes):
            if i > 0:
                tree_text.append("\n")
            self._render_node_recursive(
                tree_text, root, nodes, "", True, highlight_node, show_connections
            )
        
        return tree_text
    
    def _find_root_nodes(self, nodes: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find root nodes (those not referenced by other nodes)."""
        referenced_ids = set()
        
        # Collect all referenced node IDs
        for node in nodes.values():
            connections = node.get('connections', {})
            if isinstance(connections, dict):
                referenced_ids.update(connections.values())
            elif isinstance(connections, list):
                for conn in connections:
                    if 'target_node_id' in conn:
                        referenced_ids.add(conn['target_node_id'])
        
        # Find nodes that are not referenced by others
        root_nodes = [node for node in nodes.values() 
                     if node.get('id') not in referenced_ids]
        
        # If no clear roots found, use first node
        if not root_nodes and nodes:
            root_nodes = [list(nodes.values())[0]]
        
        return root_nodes
    
    def _render_node_recursive(self, tree_text: Text, node: Dict[str, Any],
                              all_nodes: Dict[str, Any], prefix: str, 
                              is_last: bool, highlight_node: str = None,
                              show_connections: bool = True):
        """Recursively render node and its children."""
        
        node_id = node.get('id', 'unknown')
        node_type = node.get('type', 'unknown').lower()
        
        # Choose appropriate style
        if highlight_node and node_id == highlight_node:
            style_info = self.node_styles.PROCESSING
        elif node_type == 'question':
            style_info = self.node_styles.QUESTION
        elif node_type == 'outcome':
            style_info = self.node_styles.OUTCOME
        else:
            style_info = self.node_styles.DEFAULT
        
        # Tree connector
        connector = "└── " if is_last else "├── "
        
        # Node content
        if node_type == 'question':
            content = node.get('question', 'Unknown Question')
        elif node_type == 'outcome':
            content = node.get('decision', 'Unknown Outcome') 
        else:
            content = node.get('label', node_id)
        
        # Truncate long content
        if len(content) > 60:
            content = content[:57] + "..."
        
        # Add node to tree
        tree_text.append(f"{prefix}{connector}", style="dim white")
        tree_text.append(f"{style_info['icon']} ", style=style_info['style'])
        tree_text.append(f"{content}\n", style=style_info['style'])
        
        # Add child nodes
        if show_connections:
            children = self._get_child_nodes(node, all_nodes)
            
            for i, (condition, child_node) in enumerate(children):
                is_last_child = i == len(children) - 1
                child_prefix = prefix + ("    " if is_last else "│   ")
                
                # Add condition label if available
                if condition and condition not in ['true', 'false']:
                    tree_text.append(f"{child_prefix}├─ ", style="dim white")
                    tree_text.append(f"[{condition}]\n", style="dim bright_yellow")
                    child_prefix += "│   "
                
                self._render_node_recursive(
                    tree_text, child_node, all_nodes, child_prefix,
                    is_last_child, highlight_node, show_connections
                )
    
    def _get_child_nodes(self, node: Dict[str, Any], 
                        all_nodes: Dict[str, Any]) -> List[Tuple[str, Dict[str, Any]]]:
        """Get child nodes with their connection conditions."""
        children = []
        connections = node.get('connections', {})
        
        if isinstance(connections, dict):
            for condition, target_id in connections.items():
                if target_id in all_nodes:
                    children.append((condition, all_nodes[target_id]))
        elif isinstance(connections, list):
            for conn in connections:
                target_id = conn.get('target_node_id')
                condition = conn.get('condition', '')
                if target_id in all_nodes:
                    children.append((condition, all_nodes[target_id]))
        
        return children


class RealTimeLayoutManager:
    """Manages real-time layouts for the enhanced demo."""
    
    def __init__(self, console: Console):
        self.console = console
        self.agent_renderer = AgentInsightRenderer(console)
        self.tree_renderer = UnicodeTreeRenderer()
    
    def create_processing_layout(self) -> Layout:
        """Create layout for real-time processing visualization."""
        layout = Layout()
        
        # Main layout structure
        layout.split_column(
            Layout(name="header", size=4),
            Layout(name="content"),
            Layout(name="footer", size=6)
        )
        
        # Split content area
        layout["content"].split_row(
            Layout(name="tree", ratio=3),
            Layout(name="agents", ratio=2)
        )
        
        return layout
    
    def update_layout_components(self, layout: Layout, 
                               document_name: str,
                               tree_data: Dict[str, Any],
                               agent_info: Dict[str, Any],
                               step_insights: Dict[str, Any],
                               highlight_node: str = None):
        """Update all layout components with current data."""
        
        # Header
        header_text = Text()
        header_text.append("🏥 Enhanced Decision Tree Generation\n", style="bold bright_blue") 
        header_text.append(f"📄 Processing: {document_name}", style="bright_cyan")
        
        layout["header"].update(Panel(
            header_text,
            border_style="bright_blue",
            padding=(0, 1)
        ))
        
        # Tree visualization
        tree_visual = self.tree_renderer.render_tree(tree_data, highlight_node)
        layout["tree"].update(Panel(
            tree_visual,
            title="🌳 Decision Tree (Live)",
            border_style="green",
            padding=(1, 1)
        ))
        
        # Agent panel
        if agent_info:
            agent_panel = self.agent_renderer.create_thinking_panel(
                agent_info.get('name', 'Unknown'),
                agent_info.get('step', 'Processing'),
                agent_info.get('reasoning', 'Analyzing data...'),
                agent_info.get('confidence', 0.8),
                agent_info.get('data_points', [])
            )
            layout["agents"].update(agent_panel)
        
        # Step insights footer
        if step_insights:
            insight_panel = self.agent_renderer.create_step_insight_panel(
                step_insights.get('step_name', 'Current Step'),
                step_insights.get('findings', {}),
                step_insights.get('processing_time')
            )
            layout["footer"].update(insight_panel)
    
    def animate_processing_sequence(self, document_path: str, 
                                  steps: List[Dict[str, Any]],
                                  simulate_tree_growth: bool = True):
        """Animate the complete processing sequence."""
        
        layout = self.create_processing_layout()
        tree_data = {'nodes': {}}
        
        with Live(layout, refresh_per_second=4, screen=True) as live:
            
            for i, step_info in enumerate(steps):
                # Simulate tree growth
                if simulate_tree_growth:
                    self._simulate_tree_growth(tree_data, i + 1)
                
                # Update layout with current step
                self.update_layout_components(
                    layout,
                    document_path,
                    tree_data,
                    step_info.get('agent_info', {}),
                    step_info.get('insights', {}),
                    step_info.get('highlight_node')
                )
                
                # Pause to show each step
                time.sleep(step_info.get('duration', 2.0))
    
    def _simulate_tree_growth(self, tree_data: Dict[str, Any], step: int):
        """Simulate progressive tree building for demonstration."""
        if 'nodes' not in tree_data:
            tree_data['nodes'] = {}
        
        # Progressive node addition based on step
        growth_stages = {
            1: {
                'root': {
                    'id': 'root',
                    'type': 'question', 
                    'question': 'Patient meets age criteria (≥18)?',
                    'connections': {'true': 'diagnosis', 'false': 'deny_age'}
                }
            },
            2: {
                'diagnosis': {
                    'id': 'diagnosis',
                    'type': 'question',
                    'question': 'Valid ICD-10 diagnosis confirmed?', 
                    'connections': {'true': 'insurance', 'false': 'deny_diagnosis'}
                },
                'deny_age': {
                    'id': 'deny_age',
                    'type': 'outcome',
                    'decision': 'DENY: Patient under 18 years old'
                }
            },
            3: {
                'insurance': {
                    'id': 'insurance',
                    'type': 'question',
                    'question': 'Insurance coverage verified?',
                    'connections': {'true': 'prior_auth', 'false': 'deny_insurance'}
                },
                'deny_diagnosis': {
                    'id': 'deny_diagnosis', 
                    'type': 'outcome',
                    'decision': 'DENY: Diagnosis not confirmed'
                }
            },
            4: {
                'prior_auth': {
                    'id': 'prior_auth',
                    'type': 'outcome',
                    'decision': 'APPROVE: Submit for prior authorization'
                },
                'deny_insurance': {
                    'id': 'deny_insurance',
                    'type': 'outcome', 
                    'decision': 'DENY: Insurance not verified'
                }
            }
        }
        
        # Add nodes for current and all previous steps
        for stage in range(1, step + 1):
            if stage in growth_stages:
                tree_data['nodes'].update(growth_stages[stage])


def create_demo_processing_steps() -> List[Dict[str, Any]]:
    """Create sample processing steps for demonstration."""
    return [
        {
            'agent_info': {
                'name': 'CriteriaParser',
                'step': 'Extracting eligibility criteria',
                'reasoning': 'Parsing document to identify key decision points and eligibility requirements.',
                'confidence': 0.92,
                'data_points': [
                    'Found 8 eligibility criteria',
                    'Identified age requirement: ≥18 years', 
                    'Located diagnosis validation rules'
                ]
            },
            'insights': {
                'step_name': 'Criteria Extraction',
                'findings': {
                    'key_finding': 'Document contains comprehensive eligibility matrix',
                    'impact': 'Clear decision pathways can be established',
                    'metrics': {'criteria_count': 8, 'complexity_score': 0.7}
                },
                'processing_time': 1.2
            },
            'highlight_node': 'root',
            'duration': 3.0
        },
        {
            'agent_info': {
                'name': 'TreeStructure',
                'step': 'Building decision nodes',
                'reasoning': 'Creating logical decision tree structure with proper branching and flow control.',
                'confidence': 0.87,
                'data_points': [
                    'Created 4 decision nodes',
                    'Established 6 outcome paths',
                    'Optimized tree depth to 3 levels'
                ]
            },
            'insights': {
                'step_name': 'Tree Construction',
                'findings': {
                    'key_finding': 'Optimal tree structure with balanced branching',
                    'impact': 'Efficient decision processing with minimal complexity',
                    'metrics': {'node_count': 7, 'max_depth': 3, 'branching_factor': 2.1}
                },
                'processing_time': 2.1
            },
            'highlight_node': 'diagnosis',
            'duration': 3.5
        },
        {
            'agent_info': {
                'name': 'Validation',
                'step': 'Validating logic flow',
                'reasoning': 'Checking for logical consistency, completeness, and proper error handling.',
                'confidence': 0.95,
                'data_points': [
                    'All pathways validated',
                    'No logical inconsistencies found',
                    'Complete coverage of criteria'
                ]
            },
            'insights': {
                'step_name': 'Logic Validation',
                'findings': {
                    'key_finding': 'Tree logic is consistent and complete',
                    'impact': 'High confidence in decision accuracy',
                    'metrics': {'validation_score': 0.95, 'coverage': '100%'}
                },
                'processing_time': 0.8
            },
            'highlight_node': 'insurance',
            'duration': 2.5
        },
        {
            'agent_info': {
                'name': 'Refinement',
                'step': 'Optimizing structure',
                'reasoning': 'Final optimization for clarity, efficiency, and user experience.',
                'confidence': 0.89,
                'data_points': [
                    'Simplified 2 complex nodes',
                    'Added clearer outcome descriptions',
                    'Reduced average processing path length'
                ]
            },
            'insights': {
                'step_name': 'Final Optimization',
                'findings': {
                    'key_finding': 'Structure optimized for clarity and efficiency',
                    'impact': 'Improved user experience and processing speed',
                    'metrics': {'optimization_score': 0.89, 'path_reduction': '15%'}
                },
                'processing_time': 1.5
            },
            'highlight_node': 'prior_auth',
            'duration': 2.0
        }
    ]
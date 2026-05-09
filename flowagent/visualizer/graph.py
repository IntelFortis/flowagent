"""
Workflow Graph Visualization

This module provides graph visualization for FlowAgent workflows.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Set, Tuple

from flowagent.core.workflow import Workflow
from flowagent.core.task import Task, TaskStatus


class WorkflowGraph:
    """
    Graph visualization for FlowAgent workflows.

    Example:
        >>> graph = WorkflowGraph(workflow)
        >>> print(graph.to_mermaid())
        >>> graph.save_png("workflow.png")
    """

    def __init__(self, workflow: Workflow):
        self.workflow = workflow
        self._nodes: Dict[str, Dict] = {}
        self._edges: List[Tuple[str, str]] = []

        self._build_graph()

    def _build_graph(self) -> None:
        """Build the graph structure from workflow."""
        # Add nodes
        for task_name, task in self.workflow._tasks.items():
            self._nodes[task_name] = {
                "name": task_name,
                "status": task.status.value,
                "label": task_name,
            }

        # Add edges
        for task_name, deps in self.workflow._dependencies.items():
            for dep_name in deps:
                self._edges.append((dep_name, task_name))

    def to_mermaid(self) -> str:
        """
        Generate Mermaid diagram syntax.

        Returns:
            Mermaid diagram string
        """
        lines = ["graph TD"]

        # Style definitions
        lines.append("    classDef pending fill:#e1e5e9,stroke:#333,stroke-width:2px")
        lines.append("    classDef running fill:#fff3cd,stroke:#ffc107,stroke-width:2px")
        lines.append("    classDef completed fill:#d4edda,stroke:#28a745,stroke-width:2px")
        lines.append("    classDef failed fill:#f8d7da,stroke:#dc3545,stroke-width:2px")
        lines.append("")

        # Add nodes
        for node_id, node_info in self._nodes.items():
            status = node_info["status"]
            label = node_info["label"]
            lines.append(f"    {node_id}[\"{label}\"]:::{status}")

        lines.append("")

        # Add edges
        for source, target in self._edges:
            lines.append(f"    {source} --> {target}")

        return "\n".join(lines)

    def to_dot(self) -> str:
        """
        Generate DOT (Graphviz) syntax.

        Returns:
            DOT graph string
        """
        lines = ["digraph Workflow {"]
        lines.append("    rankdir=TB;")
        lines.append("    node [shape=box, style=filled];")
        lines.append("")

        # Add nodes
        for node_id, node_info in self._nodes.items():
            status = node_info["status"]
            label = node_info["label"]

            color_map = {
                "pending": "#e1e5e9",
                "running": "#fff3cd",
                "completed": "#d4edda",
                "failed": "#f8d7da",
            }
            color = color_map.get(status, "#e1e5e9")

            lines.append(f'    {node_id} [label="{label}", fillcolor="{color}"];')

        lines.append("")

        # Add edges
        for source, target in self._edges:
            lines.append(f"    {source} -> {target};")

        lines.append("}")
        return "\n".join(lines)

    def to_ascii(self) -> str:
        """
        Generate ASCII art visualization.

        Returns:
            ASCII art string
        """
        lines = [f"Workflow: {self.workflow.name}", "=" * 50, ""]

        # Get execution order
        levels = self.workflow._get_execution_order()

        for level_idx, level in enumerate(levels):
            lines.append(f"Level {level_idx + 1}:")

            for task_name in level:
                deps = self.workflow._dependencies.get(task_name, set())
                status = self._nodes[task_name]["status"]

                # Status indicator
                status_icon = {
                    "pending": "○",
                    "running": "◉",
                    "completed": "●",
                    "failed": "✗",
                }.get(status, "?")

                if deps:
                    deps_str = ", ".join(deps)
                    lines.append(f"  {status_icon} [{task_name}] ← {deps_str}")
                else:
                    lines.append(f"  {status_icon} [{task_name}] (start)")

            lines.append("")

        return "\n".join(lines)

    def to_json(self) -> Dict:
        """
        Generate JSON representation.

        Returns:
            Dictionary with nodes and edges
        """
        return {
            "workflow": self.workflow.name,
            "nodes": list(self._nodes.values()),
            "edges": [{"source": s, "target": t} for s, t in self._edges],
        }

    def get_dependencies(self, task_name: str) -> Set[str]:
        """Get all dependencies of a task (recursive)."""
        visited: Set[str] = set()
        stack = [task_name]

        while stack:
            current = stack.pop()
            deps = self.workflow._dependencies.get(current, set())

            for dep in deps:
                if dep not in visited:
                    visited.add(dep)
                    stack.append(dep)

        return visited

    def get_dependents(self, task_name: str) -> Set[str]:
        """Get all dependents of a task (recursive)."""
        visited: Set[str] = set()
        stack = [task_name]

        while stack:
            current = stack.pop()
            deps = self.workflow._dependents.get(current, set())

            for dep in deps:
                if dep not in visited:
                    visited.add(dep)
                    stack.append(dep)

        return visited

    def get_critical_path(self) -> List[str]:
        """
        Get the critical path through the workflow.

        Returns:
            List of task names on the critical path
        """
        # Find tasks with no dependencies (start nodes)
        start_nodes = [
            name for name, deps in self.workflow._dependencies.items()
            if not deps
        ]

        if not start_nodes:
            return []

        # Find tasks with no dependents (end nodes)
        end_nodes = [
            name for name, deps in self.workflow._dependents.items()
            if not deps
        ]

        # Simple critical path (longest path)
        # For a proper critical path, we'd need task durations
        # For now, just return the first path found
        path = []
        current = start_nodes[0]

        while current:
            path.append(current)

            dependents = self.workflow._dependents.get(current, set())
            if not dependents:
                break

            current = next(iter(dependents))

        return path

    def save_mermaid(self, filename: str) -> None:
        """Save Mermaid diagram to file."""
        with open(filename, "w") as f:
            f.write(self.to_mermaid())

    def save_dot(self, filename: str) -> None:
        """Save DOT diagram to file."""
        with open(filename, "w") as f:
            f.write(self.to_dot())

    def __repr__(self) -> str:
        return f"WorkflowGraph(workflow='{self.workflow.name}', nodes={len(self._nodes)}, edges={len(self._edges)})"

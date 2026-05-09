"""
Dashboard - Real-time monitoring dashboard for FlowAgent.

This module provides a real-time dashboard for monitoring workflows.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from flowagent.core.workflow import Workflow, WorkflowStatus
from flowagent.core.task import Task, TaskStatus


class Dashboard:
    """
    Real-time monitoring dashboard for FlowAgent workflows.

    Example:
        >>> dashboard = Dashboard(workflow)
        >>> dashboard.start()  # Starts live dashboard
    """

    def __init__(self, workflow: Workflow):
        self.workflow = workflow
        self.console = Console()
        self._start_time = time.time()
        self._updates: List[Dict[str, Any]] = []

    def create_layout(self) -> Layout:
        """Create the dashboard layout."""
        layout = Layout()

        layout.split(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3),
        )

        layout["body"].split_row(
            Layout(name="tasks", ratio=2),
            Layout(name="stats", ratio=1),
        )

        return layout

    def render_header(self) -> Panel:
        """Render the header panel."""
        title = Text(f"FlowAgent Dashboard - {self.workflow.name}", style="bold blue")
        status = Text(f"Status: {self.workflow.status.value}", style="green")
        duration = time.time() - self._start_time

        header = Text.assemble(
            title, "\n",
            status, " | ",
            f"Duration: {duration:.1f}s",
        )

        return Panel(header, style="blue")

    def render_tasks_table(self) -> Table:
        """Render the tasks table."""
        table = Table(title="Tasks", show_header=True, header_style="bold magenta")

        table.add_column("Task", style="cyan", width=20)
        table.add_column("Status", width=12)
        table.add_column("Duration", width=10)
        table.add_column("Dependencies", width=20)

        for task_name, task in self.workflow._tasks.items():
            # Status styling
            status = task.status
            if status == TaskStatus.COMPLETED:
                status_text = Text("✓ Completed", style="green")
            elif status == TaskStatus.RUNNING:
                status_text = Text("◉ Running", style="yellow")
            elif status == TaskStatus.FAILED:
                status_text = Text("✗ Failed", style="red")
            elif status == TaskStatus.RETRYING:
                status_text = Text("↻ Retrying", style="yellow")
            else:
                status_text = Text("○ Pending", style="dim")

            # Duration
            if task.duration:
                duration_text = f"{task.duration:.2f}s"
            else:
                duration_text = "-"

            # Dependencies
            deps = self.workflow._dependencies.get(task_name, set())
            deps_text = ", ".join(deps) if deps else "-"

            table.add_row(
                task_name,
                status_text,
                duration_text,
                deps_text,
            )

        return table

    def render_stats_panel(self) -> Panel:
        """Render the statistics panel."""
        tasks = list(self.workflow._tasks.values())

        total = len(tasks)
        completed = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED)
        running = sum(1 for t in tasks if t.status == TaskStatus.RUNNING)
        failed = sum(1 for t in tasks if t.status == TaskStatus.FAILED)
        pending = sum(1 for t in tasks if t.status == TaskStatus.PENDING)

        stats = Text()
        stats.append("Statistics\n\n", style="bold")
        stats.append(f"Total Tasks: {total}\n")
        stats.append(f"Completed: {completed}\n", style="green")
        stats.append(f"Running: {running}\n", style="yellow")
        stats.append(f"Failed: {failed}\n", style="red")
        stats.append(f"Pending: {pending}\n", style="dim")

        # Progress bar
        if total > 0:
            progress = completed / total
            bar_length = 20
            filled = int(bar_length * progress)
            bar = "█" * filled + "░" * (bar_length - filled)
            stats.append(f"\nProgress: [{bar}] {progress:.0%}")

        return Panel(stats, title="Statistics", style="blue")

    def render_footer(self) -> Panel:
        """Render the footer panel."""
        footer = Text(
            "Press Ctrl+C to exit | ",
            style="dim",
        )
        footer.append("FlowAgent v1.0.0", style="blue")

        return Panel(footer, style="blue")

    def render(self) -> Layout:
        """Render the complete dashboard."""
        layout = self.create_layout()

        layout["header"].update(self.render_header())
        layout["tasks"].update(self.render_tasks_table())
        layout["stats"].update(self.render_stats_panel())
        layout["footer"].update(self.render_footer())

        return layout

    def start(self, refresh_per_second: float = 4) -> None:
        """
        Start the live dashboard.

        Args:
            refresh_per_second: Dashboard refresh rate
        """
        try:
            with Live(
                self.render(),
                console=self.console,
                refresh_per_second=refresh_per_second,
                screen=True,
            ) as live:
                while True:
                    live.update(self.render())
                    time.sleep(1 / refresh_per_second)

        except KeyboardInterrupt:
            self.console.print("\n[yellow]Dashboard stopped[/yellow]")

    def snapshot(self) -> Dict[str, Any]:
        """
        Take a snapshot of the current dashboard state.

        Returns:
            Dictionary with dashboard state
        """
        tasks = list(self.workflow._tasks.values())

        return {
            "workflow": self.workflow.name,
            "status": self.workflow.status.value,
            "duration": time.time() - self._start_time,
            "tasks": {
                "total": len(tasks),
                "completed": sum(1 for t in tasks if t.status == TaskStatus.COMPLETED),
                "running": sum(1 for t in tasks if t.status == TaskStatus.RUNNING),
                "failed": sum(1 for t in tasks if t.status == TaskStatus.FAILED),
                "pending": sum(1 for t in tasks if t.status == TaskStatus.PENDING),
            },
            "task_details": {
                name: {
                    "status": task.status.value,
                    "duration": task.duration,
                    "attempts": task.attempts,
                }
                for name, task in self.workflow._tasks.items()
            },
        }

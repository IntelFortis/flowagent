"""
FlowAgent CLI - Command-line interface for FlowAgent.

This module provides the CLI for running workflows and managing FlowAgent.
"""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from flowagent import __version__
from flowagent.core.logger import setup_logger

console = Console()


@click.group()
@click.version_option(version=__version__, prog_name="FlowAgent")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--log-file", type=click.Path(), help="Log file path")
def main(verbose: bool, log_file: Optional[str]) -> None:
    """
    FlowAgent - The Next-Generation Workflow Automation Framework

    Create complex workflows with just a few lines of code.
    """
    level = logging.DEBUG if verbose else logging.INFO
    setup_logger(level=level, file=log_file)


@main.command()
@click.argument("workflow_file", type=click.Path(exists=True))
@click.option("--async", "async_mode", is_flag=True, help="Run asynchronously")
def run(workflow_file: str, async_mode: bool) -> None:
    """
    Run a workflow from a file.

    WORKFLOW_FILE is the path to the workflow Python file.
    """
    try:
        # Load and execute workflow
        import importlib.util

        spec = importlib.util.spec_from_file_location("workflow", workflow_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Find workflow object (must be an instance, not the class)
        from flowagent.core.workflow import Workflow as WorkflowClass
        workflow = None
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if isinstance(attr, WorkflowClass):
                workflow = attr
                break

        if workflow is None:
            console.print("[red]Error: No workflow found in file[/red]")
            sys.exit(1)

        console.print(f"[green]Running workflow: {workflow.name}[/green]")

        # Run workflow
        if async_mode:
            results = asyncio.run(workflow.run_async())
        else:
            results = workflow.run()

        # Display results
        table = Table(title="Workflow Results")
        table.add_column("Task", style="cyan")
        table.add_column("Result", style="green")

        for task_name, result in results.items():
            table.add_row(task_name, str(result))

        console.print(table)
        console.print(f"\n[green]Workflow completed in {workflow.duration:.2f}s[/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@main.command()
@click.argument("workflow_file", type=click.Path(exists=True))
def validate(workflow_file: str) -> None:
    """
    Validate a workflow file.

    WORKFLOW_FILE is the path to the workflow Python file.
    """
    try:
        import importlib.util

        spec = importlib.util.spec_from_file_location("workflow", workflow_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Find workflow object (must be an instance, not the class)
        from flowagent.core.workflow import Workflow as WorkflowClass
        workflow = None
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if isinstance(attr, WorkflowClass):
                workflow = attr
                break

        if workflow is None:
            console.print("[red]Error: No workflow found in file[/red]")
            sys.exit(1)

        # Validate workflow
        console.print(f"[green]Validating workflow: {workflow.name}[/green]")
        console.print(f"  Tasks: {len(workflow)}")
        console.print(f"  Status: {workflow.status.value}")

        # Visualize
        console.print("\n[bold]Workflow Structure:[/bold]")
        console.print(workflow.visualize())

        console.print("\n[green]Workflow is valid![/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@main.command()
def version() -> None:
    """Show FlowAgent version."""
    console.print(f"FlowAgent v{__version__}")


@main.command()
def info() -> None:
    """Show FlowAgent information."""
    table = Table(title="FlowAgent Information")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Version", __version__)
    table.add_row("Python", sys.version.split()[0])
    table.add_row("Platform", sys.platform)

    console.print(table)


@main.command()
@click.argument("output_dir", type=click.Path(), default=".")
def init(output_dir: str) -> None:
    """
    Initialize a new FlowAgent project.

    OUTPUT_DIR is the directory to initialize (default: current directory).
    """
    try:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Create project structure
        (output_path / "workflows").mkdir(exist_ok=True)
        (output_path / "tasks").mkdir(exist_ok=True)
        (output_path / "config").mkdir(exist_ok=True)

        # Create example workflow
        example_workflow = '''"""
Example FlowAgent Workflow

This is an example workflow to get you started with FlowAgent.
"""

from flowagent import Workflow, task


@task
def hello():
    """Say hello."""
    return "Hello, FlowAgent!"


@task
def process(ctx):
    """Process the greeting."""
    greeting = ctx.get("dep:hello")
    return f"{greeting} - Processed!"


def create_workflow():
    """Create and return the workflow."""
    workflow = Workflow("example")
    workflow.add(hello)
    workflow.add(process, depends_on=[hello])
    return workflow


if __name__ == "__main__":
    workflow = create_workflow()
    results = workflow.run()
    print(results)
'''

        (output_path / "workflows" / "example.py").write_text(example_workflow)

        # Create config file
        config = '''# FlowAgent Configuration
# See documentation for all available options

workflow:
  max_parallel_tasks: 10
  timeout: 300

logging:
  level: INFO
  file: flowagent.log

integrations:
  # Uncomment and configure as needed
  # openai:
  #   api_key: ${OPENAI_API_KEY}
  #   model: gpt-4
  # postgres:
  #   connection_string: ${DATABASE_URL}
'''

        (output_path / "config" / "flowagent.yaml").write_text(config)

        # Create README
        readme = '''# FlowAgent Project

This is a FlowAgent workflow automation project.

## Quick Start

```bash
# Install FlowAgent
pip install flowagent

# Run the example workflow
flowagent run workflows/example.py

# Validate workflow
flowagent validate workflows/example.py
```

## Project Structure

```
.
├── workflows/      # Workflow definitions
├── tasks/          # Reusable task definitions
├── config/         # Configuration files
└── README.md       # This file
```

## Documentation

See [FlowAgent Documentation](https://flowagent.dev) for more information.
'''

        (output_path / "README.md").write_text(readme)

        console.print(f"[green]FlowAgent project initialized in {output_path}[/green]")
        console.print("\nProject structure:")
        console.print("  workflows/    - Workflow definitions")
        console.print("  tasks/        - Reusable task definitions")
        console.print("  config/       - Configuration files")
        console.print("\nNext steps:")
        console.print("  1. Edit workflows/example.py")
        console.print("  2. Run: flowagent run workflows/example.py")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@main.command()
@click.option("--host", default="127.0.0.1", help="Host to bind")
@click.option("--port", "-p", default=8000, type=int, help="Port to listen on")
@click.option("--reload", is_flag=True, help="Enable auto-reload for development")
def ui(host: str, port: int, reload: bool) -> None:
    """
    Launch the FlowAgent visual workflow editor.

    Opens a web-based UI for creating workflows by dragging and dropping nodes.
    """
    try:
        import uvicorn
    except ImportError:
        console.print("[red]Error: uvicorn is required for the UI server.[/red]")
        console.print("Install it with: pip install uvicorn")
        sys.exit(1)

    console.print(f"[green]Starting FlowAgent UI...[/green]")
    console.print(f"[cyan]Open http://localhost:{port} in your browser[/cyan]")

    uvicorn.run(
        "flowagent.server.app:create_app",
        factory=True,
        host=host,
        port=port,
        reload=reload,
    )


if __name__ == "__main__":
    main()

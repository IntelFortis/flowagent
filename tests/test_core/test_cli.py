"""Tests for CLI commands."""

import pytest
from click.testing import CliRunner

from flowagent.cli import main


@pytest.fixture
def runner():
    return CliRunner()


class TestCLI:
    def test_version(self, runner):
        result = runner.invoke(main, ["version"])
        assert result.exit_code == 0
        assert "FlowAgent v" in result.output

    def test_info(self, runner):
        result = runner.invoke(main, ["info"])
        assert result.exit_code == 0
        assert "Version" in result.output
        assert "Python" in result.output
        assert "Platform" in result.output

    def test_validate_missing_file(self, runner):
        result = runner.invoke(main, ["validate", "nonexistent.py"])
        assert result.exit_code != 0

    def test_validate_workflow(self, runner, tmp_path):
        workflow_file = tmp_path / "test_workflow.py"
        workflow_file.write_text('''
from flowagent import Workflow, task

@task
def hello():
    return "Hello"

workflow = Workflow("test")
workflow.add(hello)
''')
        result = runner.invoke(main, ["validate", str(workflow_file)])
        assert result.exit_code == 0
        assert "Validating workflow" in result.output
        assert "valid" in result.output.lower()

    def test_run_workflow(self, runner, tmp_path):
        workflow_file = tmp_path / "test_workflow.py"
        workflow_file.write_text('''
from flowagent import Workflow, task

@task
def hello():
    return "Hello, World!"

workflow = Workflow("test")
workflow.add(hello)
''')
        result = runner.invoke(main, ["run", str(workflow_file)])
        assert result.exit_code == 0
        assert "Hello, World!" in result.output

    def test_init_creates_structure(self, runner, tmp_path):
        result = runner.invoke(main, ["init", str(tmp_path / "myproject")])
        assert result.exit_code == 0
        assert (tmp_path / "myproject" / "workflows").exists()
        assert (tmp_path / "myproject" / "tasks").exists()
        assert (tmp_path / "myproject" / "config").exists()
        assert (tmp_path / "myproject" / "workflows" / "example.py").exists()

    def test_verbose_flag(self, runner):
        result = runner.invoke(main, ["--verbose", "version"])
        assert result.exit_code == 0

"""Tests for workflow visualizer."""

import pytest

from flowagent import Workflow, task
from flowagent.visualizer.graph import WorkflowGraph


@pytest.fixture
def sample_workflow():
    @task
    def step_a():
        return "a"

    @task
    def step_b():
        return "b"

    @task
    def step_c():
        return "c"

    workflow = Workflow("test-viz")
    workflow.add(step_a)
    workflow.add(step_b, depends_on=[step_a])
    workflow.add(step_c, depends_on=[step_a])
    return workflow


class TestWorkflowGraph:
    def test_build_graph(self, sample_workflow):
        graph = WorkflowGraph(sample_workflow)
        assert len(graph._nodes) == 3
        assert len(graph._edges) == 2

    def test_to_mermaid(self, sample_workflow):
        graph = WorkflowGraph(sample_workflow)
        mermaid = graph.to_mermaid()
        assert "graph TD" in mermaid
        assert "step_a" in mermaid
        assert "step_b" in mermaid
        assert "-->" in mermaid

    def test_to_dot(self, sample_workflow):
        graph = WorkflowGraph(sample_workflow)
        dot = graph.to_dot()
        assert "digraph Workflow" in dot
        assert "step_a" in dot
        assert "->" in dot

    def test_to_ascii(self, sample_workflow):
        graph = WorkflowGraph(sample_workflow)
        ascii_art = graph.to_ascii()
        assert "test-viz" in ascii_art
        assert "step_a" in ascii_art

    def test_to_json(self, sample_workflow):
        graph = WorkflowGraph(sample_workflow)
        data = graph.to_json()
        assert data["workflow"] == "test-viz"
        assert len(data["nodes"]) == 3
        assert len(data["edges"]) == 2

    def test_get_dependencies(self, sample_workflow):
        graph = WorkflowGraph(sample_workflow)
        deps = graph.get_dependencies("step_b")
        assert "step_a" in deps

    def test_get_dependents(self, sample_workflow):
        graph = WorkflowGraph(sample_workflow)
        dependents = graph.get_dependents("step_a")
        assert "step_b" in dependents
        assert "step_c" in dependents

    def test_get_critical_path(self, sample_workflow):
        graph = WorkflowGraph(sample_workflow)
        path = graph.get_critical_path()
        assert len(path) >= 1
        assert path[0] == "step_a"

    def test_repr(self, sample_workflow):
        graph = WorkflowGraph(sample_workflow)
        r = repr(graph)
        assert "test-viz" in r
        assert "nodes=3" in r

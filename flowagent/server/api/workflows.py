"""Workflow CRUD and execution API."""

from __future__ import annotations

import asyncio
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(tags=["workflows"])


# In-memory storage for local experimentation. Use persistent storage for deployments.
_workflows: Dict[str, Dict[str, Any]] = {}
_executions: Dict[str, Dict[str, Any]] = {}


# --- Pydantic models ---

class NodeData(BaseModel):
    model_config = {"extra": "allow"}
    type: str
    label: str
    config: Dict[str, Any] = Field(default_factory=dict)


class NodeModel(BaseModel):
    model_config = {"extra": "allow"}
    id: str
    type: str
    position: Dict[str, float]
    data: NodeData
    width: Optional[int] = None
    height: Optional[int] = None


class EdgeModel(BaseModel):
    model_config = {"extra": "allow"}
    id: str
    source: str
    target: str
    sourceHandle: Optional[str] = None
    targetHandle: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class WorkflowCreate(BaseModel):
    name: str
    description: str = ""
    tags: List[str] = Field(default_factory=list)
    nodes: List[NodeModel] = Field(default_factory=list)
    edges: List[EdgeModel] = Field(default_factory=list)


class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    nodes: Optional[List[NodeModel]] = None
    edges: Optional[List[EdgeModel]] = None


class RunOptions(BaseModel):
    global_api_key: str = ""
    global_api_base: str = ""
    global_model: str = ""


class WorkflowResponse(BaseModel):
    id: str
    name: str
    description: str
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    status: str = "idle"
    created_at: str
    updated_at: str


# --- Helper ---

def _now_iso() -> str:
    from datetime import datetime
    return datetime.now().isoformat()


# --- Routes ---

@router.get("/workflows")
async def list_workflows() -> List[Dict[str, Any]]:
    """List all workflows."""
    result = []
    for wf in _workflows.values():
        # Find latest execution for this workflow
        latest_exec = None
        for exec in _executions.values():
            if exec["workflow_id"] == wf["id"]:
                if latest_exec is None or exec["started_at"] > latest_exec["started_at"]:
                    latest_exec = exec

        entry = {
            "id": wf["id"],
            "name": wf["name"],
            "description": wf["description"],
            "tags": wf.get("tags", []),
            "status": wf["status"],
            "node_count": len(wf["nodes"]),
            "created_at": wf["created_at"],
            "updated_at": wf["updated_at"],
        }
        if latest_exec:
            entry["last_execution"] = {
                "status": latest_exec["status"],
                "started_at": latest_exec["started_at"],
                "finished_at": latest_exec.get("finished_at"),
                "duration_ms": latest_exec.get("duration_ms"),
            }
        result.append(entry)
    return result


@router.post("/workflows")
async def create_workflow(body: WorkflowCreate) -> Dict[str, Any]:
    """Create a new workflow."""
    wf_id = str(uuid.uuid4())[:8]
    now = _now_iso()
    wf = {
        "id": wf_id,
        "name": body.name,
        "description": body.description,
        "tags": body.tags,
        "nodes": [n.model_dump() for n in body.nodes],
        "edges": [e.model_dump() for e in body.edges],
        "status": "idle",
        "created_at": now,
        "updated_at": now,
    }
    _workflows[wf_id] = wf
    return wf


@router.get("/workflows/{wf_id}")
async def get_workflow(wf_id: str) -> Dict[str, Any]:
    """Get a workflow by ID."""
    if wf_id not in _workflows:
        raise HTTPException(404, "Workflow not found")
    return _workflows[wf_id]


@router.put("/workflows/{wf_id}")
async def update_workflow(wf_id: str, body: WorkflowUpdate) -> Dict[str, Any]:
    """Update a workflow."""
    if wf_id not in _workflows:
        raise HTTPException(404, "Workflow not found")
    wf = _workflows[wf_id]
    if body.name is not None:
        wf["name"] = body.name
    if body.description is not None:
        wf["description"] = body.description
    if body.tags is not None:
        wf["tags"] = body.tags
    if body.nodes is not None:
        wf["nodes"] = [n.model_dump() for n in body.nodes]
    if body.edges is not None:
        wf["edges"] = [e.model_dump() for e in body.edges]
    wf["updated_at"] = _now_iso()
    return wf


@router.delete("/workflows/{wf_id}")
async def delete_workflow(wf_id: str) -> Dict[str, str]:
    """Delete a workflow."""
    if wf_id not in _workflows:
        raise HTTPException(404, "Workflow not found")
    del _workflows[wf_id]
    # Clean up orphaned executions
    exec_ids_to_remove = [eid for eid, e in _executions.items() if e["workflow_id"] == wf_id]
    for eid in exec_ids_to_remove:
        del _executions[eid]
    return {"status": "deleted"}


@router.post("/workflows/{wf_id}/run")
async def run_workflow(wf_id: str, body: RunOptions = RunOptions()) -> Dict[str, Any]:
    """Execute a workflow."""
    if wf_id not in _workflows:
        raise HTTPException(404, "Workflow not found")

    wf = _workflows[wf_id]
    exec_id = str(uuid.uuid4())[:8]

    # Build execution context from nodes
    execution = {
        "id": exec_id,
        "workflow_id": wf_id,
        "status": "running",
        "node_statuses": {},
        "logs": [],
        "results": {},
        "started_at": _now_iso(),
        "finished_at": None,
        "global_settings": {
            "api_key": body.global_api_key,
            "api_base": body.global_api_base,
            "model": body.global_model,
        },
    }

    # Initialize all nodes as pending
    for node in wf["nodes"]:
        execution["node_statuses"][node["id"]] = "pending"

    _executions[exec_id] = execution
    wf["status"] = "running"

    # Run in background
    asyncio.create_task(_execute_workflow(wf, execution))

    return execution


@router.post("/workflows/{wf_id}/stop")
async def stop_workflow(wf_id: str) -> Dict[str, str]:
    """Stop a running workflow."""
    if wf_id not in _workflows:
        raise HTTPException(404, "Workflow not found")
    wf = _workflows[wf_id]
    wf["status"] = "stopped"
    # Also update the latest execution status
    for exec in _executions.values():
        if exec["workflow_id"] == wf_id and exec["status"] == "running":
            exec["status"] = "stopped"
            exec["finished_at"] = _now_iso()
    return {"status": "stopped"}


@router.get("/workflows/{wf_id}/status")
async def get_workflow_status(wf_id: str) -> Dict[str, Any]:
    """Get workflow execution status."""
    if wf_id not in _workflows:
        raise HTTPException(404, "Workflow not found")

    # Find latest execution
    latest = None
    for exec in _executions.values():
        if exec["workflow_id"] == wf_id:
            if latest is None or exec["started_at"] > latest["started_at"]:
                latest = exec

    if latest is None:
        return {"status": "idle", "execution": None}

    return {"status": latest["status"], "execution": latest}


@router.get("/workflows/{wf_id}/executions")
async def list_executions(wf_id: str) -> List[Dict[str, Any]]:
    """List executions for a workflow, newest first."""
    execs = [
        {
            "id": e["id"],
            "workflow_id": e["workflow_id"],
            "status": e["status"],
            "started_at": e["started_at"],
            "finished_at": e["finished_at"],
            "duration_ms": (
                int((__import__("datetime").datetime.fromisoformat(e["finished_at"]) - __import__("datetime").datetime.fromisoformat(e["started_at"])).total_seconds() * 1000)
                if e["finished_at"] else None
            ),
            "node_count": len(e["node_statuses"]),
            "failed_nodes": sum(1 for s in e["node_statuses"].values() if s == "failed"),
            "log_count": len(e["logs"]),
        }
        for e in _executions.values()
        if e["workflow_id"] == wf_id
    ]
    execs.sort(key=lambda x: x["started_at"], reverse=True)
    return execs


@router.get("/executions/{exec_id}")
async def get_execution(exec_id: str) -> Dict[str, Any]:
    """Get full execution details including logs."""
    if exec_id not in _executions:
        raise HTTPException(404, "Execution not found")
    return _executions[exec_id]


async def _execute_workflow(wf: Dict[str, Any], execution: Dict[str, Any]) -> None:
    """Execute workflow with real node executors and variable passing."""
    from flowagent.server.api.executors import execute_node, resolve_variables

    global_settings = execution.get("global_settings", {})

    try:
        nodes = wf["nodes"]
        edges = wf["edges"]

        # Build adjacency
        in_degree = {n["id"]: 0 for n in nodes}
        dependents: Dict[str, List[str]] = {n["id"]: [] for n in nodes}
        upstream_map: Dict[str, List[str]] = {n["id"]: [] for n in nodes}
        for edge in edges:
            in_degree[edge["target"]] += 1
            dependents[edge["source"]].append(edge["target"])
            upstream_map[edge["target"]].append(edge["source"])

        # Variable context: stores output of each executed node
        node_context: Dict[str, Any] = {}

        # Build label-to-id mapping for user-friendly variable references
        label_map: Dict[str, str] = {}
        for n in nodes:
            label = n["data"].get("label", n["id"])
            label_map[label] = n["id"]

        # Topological execution
        queue = [nid for nid, deg in in_degree.items() if deg == 0]

        while queue:
            if wf["status"] == "stopped":
                execution["status"] = "stopped"
                execution["finished_at"] = _now_iso()
                return

            next_queue = []
            for node_id in queue:
                node = next(n for n in nodes if n["id"] == node_id)
                node_type = node["data"]["type"]
                config = node["data"].get("config", {})

                execution["node_statuses"][node_id] = "running"
                execution["logs"].append({
                    "time": _now_iso(),
                    "node": node_id,
                    "message": f"执行 {node['data']['label']}...",
                    "level": "info",
                })

                # Gather input from upstream nodes
                input_data = None
                upstream_ids = upstream_map[node_id]
                if upstream_ids:
                    if len(upstream_ids) == 1:
                        # Single upstream: pass its output directly
                        upstream_result = node_context.get(upstream_ids[0], {})
                        input_data = upstream_result.get("output", upstream_result)
                    else:
                        # Multiple upstream: aggregate into dict
                        input_data = {}
                        for uid in upstream_ids:
                            upstream_result = node_context.get(uid, {})
                            input_data[uid] = upstream_result.get("output", upstream_result)

                # Add all node outputs to context for template variable resolution
                full_context = {}
                for nid, result in node_context.items():
                    full_context[nid] = result.get("output", result) if isinstance(result, dict) else result

                try:
                    # Execute the node
                    result = await execute_node(node_type, config, input_data, full_context, label_map, global_settings)

                    # Store result in context
                    node_context[node_id] = {"output": result}

                    # Determine if node failed
                    has_error = isinstance(result, dict) and "error" in result and result.get("error")

                    execution["node_statuses"][node_id] = "failed" if has_error else "completed"
                    execution["results"][node_id] = result

                    level = "error" if has_error else "success"
                    msg = result.get("error", "") if has_error else f"{node['data']['label']} 完成"
                    execution["logs"].append({
                        "time": _now_iso(),
                        "node": node_id,
                        "message": msg if has_error else f"{node['data']['label']} 执行完成",
                        "level": level,
                    })

                    # If a node fails, mark downstream as skipped
                    if has_error:
                        for dep in dependents[node_id]:
                            execution["node_statuses"][dep] = "skipped"
                            execution["logs"].append({
                                "time": _now_iso(),
                                "node": dep,
                                "message": f"跳过: 上游节点 {node_id} 执行失败",
                                "level": "warning",
                            })

                except Exception as e:
                    execution["node_statuses"][node_id] = "failed"
                    execution["results"][node_id] = {"error": str(e)}
                    execution["logs"].append({
                        "time": _now_iso(),
                        "node": node_id,
                        "message": f"执行失败: {e}",
                        "level": "error",
                    })

                for dep in dependents[node_id]:
                    in_degree[dep] -= 1
                    if in_degree[dep] == 0:
                        next_queue.append(dep)

            queue = next_queue

        # Check if any node failed
        failed = any(s == "failed" for s in execution["node_statuses"].values())
        execution["status"] = "failed" if failed else "completed"
        execution["finished_at"] = _now_iso()
        wf["status"] = execution["status"]

    except Exception as e:
        execution["status"] = "failed"
        execution["finished_at"] = _now_iso()
        execution["logs"].append({
            "time": _now_iso(),
            "node": "",
            "message": str(e),
            "level": "error",
        })
        wf["status"] = "failed"

from __future__ import annotations

from fastapi import FastAPI, HTTPException

from app.agent import WorkflowAutomationAgent
from app.memory import MemoryStore, to_context
from app.models import ExecuteRequest, ExecuteResponse
from app.tools import build_tools

app = FastAPI(title="AI Workflow Automation Agent", version="0.1.0")

memory = MemoryStore()
tools = build_tools()
agent = WorkflowAutomationAgent(tools=tools, memory=memory)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/tools")
def list_tools() -> dict[str, list[str]]:
    return {"tools": tools.list_tools()}


@app.post("/execute", response_model=ExecuteResponse)
def execute_workflow(request: ExecuteRequest) -> ExecuteResponse:
    return agent.execute(request)


@app.get("/tasks/{task_id}")
def get_task(task_id: str) -> dict:
    task = agent.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task.model_dump()


@app.get("/memory/{user_id}")
def get_memory(user_id: str) -> dict:
    recent = memory.recent(user_id)
    return {
        "recent": to_context(recent),
        "semantic_example": to_context(memory.semantic_search(user_id, "sales summary")),
    }

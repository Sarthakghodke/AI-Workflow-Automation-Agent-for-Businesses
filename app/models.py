from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class ActionStep(BaseModel):
    tool: str
    description: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class ExecuteRequest(BaseModel):
    user_id: str = Field(..., description="Business user who requested the automation")
    instruction: str = Field(..., description="Natural language workflow request")
    context: dict[str, Any] = Field(default_factory=dict)


class ExecuteResponse(BaseModel):
    task_id: str
    status: TaskStatus
    plan: list[ActionStep]
    outputs: list[dict[str, Any]]
    summary: str


class TaskRecord(BaseModel):
    task_id: str
    user_id: str
    instruction: str
    status: TaskStatus = TaskStatus.pending
    plan: list[ActionStep] = Field(default_factory=list)
    outputs: list[dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ToolResult(BaseModel):
    tool: str
    ok: bool
    message: str
    payload: dict[str, Any] = Field(default_factory=dict)


class MemoryEntry(BaseModel):
    kind: Literal["conversation", "task", "note"]
    user_id: str
    text: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)

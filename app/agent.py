from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from app.memory import MemoryStore
from app.models import ActionStep, ExecuteRequest, ExecuteResponse, MemoryEntry, TaskRecord, TaskStatus
from app.tools import ToolRegistry


class WorkflowAutomationAgent:
    """A lightweight AI workflow orchestration layer.

    In production this planner would call an LLM (GPT/Claude/Llama) for reasoning,
    then execute the selected tools through a secure tool-calling interface.
    """

    def __init__(self, tools: ToolRegistry, memory: MemoryStore) -> None:
        self.tools = tools
        self.memory = memory
        self.tasks: dict[str, TaskRecord] = {}

    def execute(self, request: ExecuteRequest) -> ExecuteResponse:
        task_id = str(uuid.uuid4())
        plan = self._plan(request.instruction, request.context)

        record = TaskRecord(
            task_id=task_id,
            user_id=request.user_id,
            instruction=request.instruction,
            status=TaskStatus.running,
            plan=plan,
        )
        self.tasks[task_id] = record

        self.memory.add(
            MemoryEntry(
                kind="conversation",
                user_id=request.user_id,
                text=request.instruction,
                metadata={"task_id": task_id},
            )
        )

        outputs: list[dict[str, Any]] = []
        for step in plan:
            result = self.tools.run(step.tool, step.arguments)
            outputs.append(result.model_dump())
            if not result.ok:
                record.status = TaskStatus.failed
                record.outputs = outputs
                record.updated_at = datetime.utcnow()
                return ExecuteResponse(
                    task_id=task_id,
                    status=record.status,
                    plan=plan,
                    outputs=outputs,
                    summary=f"Task failed during tool `{step.tool}`: {result.message}",
                )

        record.status = TaskStatus.completed
        record.outputs = outputs
        record.updated_at = datetime.utcnow()

        summary = self._summarize(plan, outputs)
        self.memory.add(
            MemoryEntry(
                kind="task",
                user_id=request.user_id,
                text=summary,
                metadata={"task_id": task_id, "status": record.status.value},
            )
        )

        return ExecuteResponse(
            task_id=task_id,
            status=record.status,
            plan=plan,
            outputs=outputs,
            summary=summary,
        )

    def get_task(self, task_id: str) -> TaskRecord | None:
        return self.tasks.get(task_id)

    def _plan(self, instruction: str, context: dict[str, Any]) -> list[ActionStep]:
        text = instruction.lower()
        plan: list[ActionStep] = []

        if "sales" in text and "summary" in text:
            week = context.get("week", "2026-W11")
            plan.append(
                ActionStep(
                    tool="sql_query",
                    description="Fetch weekly sales totals",
                    arguments={
                        "query": (
                            "SELECT salesperson, SUM(amount) AS total_amount "
                            f"FROM sales WHERE week = '{week}' GROUP BY salesperson"
                        )
                    },
                )
            )
            plan.append(
                ActionStep(
                    tool="report_generator",
                    description="Generate sales summary report",
                    arguments={
                        "title": f"Sales Summary - {week}",
                        "body": "Automatically generated summary from SQL results.",
                        "filename": f"sales-summary-{week}.txt",
                    },
                )
            )

        if "email" in text:
            recipients = context.get("recipients", ["management@company.com"])
            plan.append(
                ActionStep(
                    tool="email_sender",
                    description="Email summary to stakeholders",
                    arguments={
                        "to": recipients,
                        "subject": "Automated Business Summary",
                        "body": "Generated report is ready.",
                    },
                )
            )

        if "meeting" in text and ("summarize" in text or "summary" in text):
            plan.append(
                ActionStep(
                    tool="meeting_summarizer",
                    description="Summarize meeting transcript",
                    arguments={"transcript": context.get("transcript", "")},
                )
            )

        if "crm" in text or "update customer" in text:
            plan.append(
                ActionStep(
                    tool="crm_update",
                    description="Write activity note into CRM",
                    arguments={
                        "customer_id": context.get("customer_id", "CUST-001"),
                        "note": context.get("crm_note", "Automated follow-up logged."),
                    },
                )
            )

        if not plan:
            plan.append(
                ActionStep(
                    tool="report_generator",
                    description="Capture unsupported request into an operations report",
                    arguments={
                        "title": "Unhandled Automation Request",
                        "body": f"Instruction: {instruction}",
                        "filename": "unhandled-request.txt",
                    },
                )
            )

        return plan

    @staticmethod
    def _summarize(plan: list[ActionStep], outputs: list[dict[str, Any]]) -> str:
        successful = sum(1 for result in outputs if result.get("ok"))
        return (
            f"Executed {len(plan)} planned steps with {successful} successful tool calls. "
            "Outputs include database extraction, artifacts, and automation actions."
        )

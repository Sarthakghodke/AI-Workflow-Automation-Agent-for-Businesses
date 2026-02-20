from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Callable

from app.models import ToolResult

ToolHandler = Callable[[dict[str, Any]], ToolResult]


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolHandler] = {}

    def register(self, name: str, handler: ToolHandler) -> None:
        self._tools[name] = handler

    def run(self, name: str, args: dict[str, Any]) -> ToolResult:
        if name not in self._tools:
            return ToolResult(tool=name, ok=False, message=f"Unknown tool: {name}")
        return self._tools[name](args)

    def list_tools(self) -> list[str]:
        return sorted(self._tools.keys())


def build_tools(db_path: str = "data/business.db", out_dir: str = "data/reports") -> ToolRegistry:
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    _ensure_seed_data(db_path)

    registry = ToolRegistry()

    def sql_query_tool(args: dict[str, Any]) -> ToolResult:
        query = args.get("query", "")
        if not query:
            return ToolResult(tool="sql_query", ok=False, message="Missing SQL query")

        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(query).fetchall()
        payload = {"rows": [dict(row) for row in rows], "count": len(rows)}
        return ToolResult(tool="sql_query", ok=True, message="Query executed", payload=payload)

    def report_generator_tool(args: dict[str, Any]) -> ToolResult:
        title = args.get("title", "Business Report")
        body = args.get("body", "No content")
        filename = args.get("filename", "report.txt")
        destination = Path(out_dir) / filename
        destination.write_text(f"# {title}\n\n{body}\n", encoding="utf-8")
        return ToolResult(
            tool="report_generator",
            ok=True,
            message="Report generated",
            payload={"path": str(destination)},
        )

    def email_sender_tool(args: dict[str, Any]) -> ToolResult:
        payload = {
            "to": args.get("to", ["management@company.com"]),
            "subject": args.get("subject", "Automated update"),
            "body": args.get("body", "See attached report."),
        }
        log_path = Path(out_dir) / "email_log.json"
        previous = []
        if log_path.exists():
            previous = json.loads(log_path.read_text(encoding="utf-8"))
        previous.append(payload)
        log_path.write_text(json.dumps(previous, indent=2), encoding="utf-8")
        return ToolResult(tool="email_sender", ok=True, message="Email queued", payload=payload)

    def crm_update_tool(args: dict[str, Any]) -> ToolResult:
        customer_id = args.get("customer_id", "unknown")
        note = args.get("note", "")
        with sqlite3.connect(db_path) as conn:
            conn.execute(
                "INSERT INTO crm_updates(customer_id, note) VALUES (?, ?)",
                (customer_id, note),
            )
            conn.commit()
        return ToolResult(
            tool="crm_update",
            ok=True,
            message="CRM updated",
            payload={"customer_id": customer_id, "note": note},
        )

    def meeting_summarizer_tool(args: dict[str, Any]) -> ToolResult:
        transcript = args.get("transcript", "")
        max_sentences = int(args.get("max_sentences", 3))
        sentences = [s.strip() for s in transcript.split(".") if s.strip()]
        summary = ". ".join(sentences[:max_sentences]) + ("." if sentences else "")
        return ToolResult(
            tool="meeting_summarizer",
            ok=True,
            message="Meeting summarized",
            payload={"summary": summary},
        )

    registry.register("sql_query", sql_query_tool)
    registry.register("report_generator", report_generator_tool)
    registry.register("email_sender", email_sender_tool)
    registry.register("crm_update", crm_update_tool)
    registry.register("meeting_summarizer", meeting_summarizer_tool)

    return registry


def _ensure_seed_data(db_path: str) -> None:
    db_file = Path(db_path)
    db_file.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                salesperson TEXT,
                amount REAL,
                week TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS crm_updates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id TEXT,
                note TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        count = conn.execute("SELECT COUNT(*) FROM sales").fetchone()[0]
        if count == 0:
            conn.executemany(
                "INSERT INTO sales(salesperson, amount, week) VALUES (?, ?, ?)",
                [
                    ("Asha", 9200, "2026-W10"),
                    ("Kai", 11500, "2026-W10"),
                    ("Asha", 8700, "2026-W11"),
                    ("Kai", 9900, "2026-W11"),
                ],
            )
        conn.commit()

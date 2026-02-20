# AI Workflow Automation Agent for Businesses

An **AI employee assistant backend** focused on workflow automation, not chat.

This project demonstrates a multi-step agent that can:
- Read natural language instructions
- Plan task steps
- Call tools (SQL query, report generation, email sending, meeting summarization, CRM updates)
- Persist task outcomes and searchable memory
- Return an execution summary through an API

## Architecture

### 1) LLM Brain (planner layer)
`WorkflowAutomationAgent` acts as the reasoning/planning layer. In this starter project, planning is deterministic/rule-based, but the same interface is designed so you can plug GPT/Claude/Llama for tool-selection reasoning.

### 2) Tool Calling System
Tools are registered in `ToolRegistry` and invoked by name:
- `sql_query`
- `report_generator`
- `email_sender`
- `meeting_summarizer`
- `crm_update`

### 3) Memory System
`MemoryStore` includes:
- short-term recent memory (`recent`)
- lightweight semantic retrieval (`semantic_search`) via bag-of-words cosine similarity

### 4) Backend
- FastAPI API server
- SQLite seed DB for demo business data (`data/business.db`)
- File artifacts for reports + email logs (`data/reports/`)

### 5) Agent Framework Pattern
The app follows an agentic cycle:
1. Parse instruction
2. Build plan
3. Execute tools sequentially
4. Save task + memory
5. Return summary and outputs

## API Endpoints

- `GET /health` — service status
- `GET /tools` — available tools
- `POST /execute` — run automation instruction
- `GET /tasks/{task_id}` — fetch task record
- `GET /memory/{user_id}` — view recent and semantically relevant memory

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Example request

```bash
curl -X POST http://127.0.0.1:8000/execute \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "ops-manager-7",
    "instruction": "Generate this week\'s sales summary and email it to management",
    "context": {
      "week": "2026-W11",
      "recipients": ["management@company.com"]
    }
  }'
```

## Test

```bash
pytest -q
```

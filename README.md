# AI Companion — Memory & Evaluation

An AI companion focused on persistent memory, retrieval, contradiction handling,
and personality consistency.

This repository is currently a **scaffold**: filesystem, dependencies, and
boilerplate interfaces only. Memory, RAG, agent, validation, and conversation
logic are not implemented yet.

## Stack

- Python 3.10.12
- [uv](https://docs.astral.sh/uv/) for dependency management
- Pydantic v2 / Pydantic Settings
- SQLModel + SQLite
- OpenAI Python SDK
- Pinecone Python SDK

## Setup

```bash
uv sync
cp .env.example .env  # fill in API keys
uv run python src/main.py
```

## Project Structure

```
src/
├── agents/         # application-level AI agents and orchestration
├── db/             # SQLite + SQLModel connection/session scaffolding
├── models/         # SQLModel database models
├── repositories/   # database persistence abstractions
├── services/       # integrations with external AI/retrieval systems (OpenAI, Pinecone)
├── prompts/        # prompt construction
├── schemas/        # Pydantic input/output contracts
├── config.py       # environment-based configuration
└── main.py         # application entry point
```

See `CLAUDE.md` for architectural conventions.

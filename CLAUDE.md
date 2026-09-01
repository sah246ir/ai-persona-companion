# CLAUDE.md

Guidance for working in this repository.

## Status

This project is currently a scaffold. Memory, RAG, agent reasoning, and
validation logic are not yet implemented — only interfaces/boilerplate exist.
Do not add real business logic unless explicitly asked.

## Dependency Direction

```
agents
    ↓
services / repositories
    ↓
external systems / database
```

- `agents/` may use `services/`, `repositories/`, `prompts/`, and `schemas/`.
- `services/` handle external integrations (OpenAI, Pinecone). Only services
  talk to external APIs.
- `repositories/` handle database persistence only. Never put OpenAI or
  Pinecone logic in a repository.
- `models/` define SQLModel database entities.
- `schemas/` define Pydantic contracts for application/LLM input and output.
- `prompts/` contain prompt construction functions.

Keep this direction one-way — do not import "up" the stack (e.g. a service
importing an agent).

## Conventions

- No unnecessary abstractions or base classes.
- Configuration is environment-based via `src/config.py` (Pydantic Settings).
  Never hardcode credentials.
- No test directory currently exists.

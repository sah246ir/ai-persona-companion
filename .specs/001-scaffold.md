# Project: AI Companion — Memory & Evaluation

Scaffold a Python project for an AI companion focused on persistent memory,
retrieval, contradiction handling, and personality consistency.

This is ONLY a project scaffold.

Create the filesystem, dependencies, configuration, and basic boilerplate
classes/functions. Do NOT implement the actual memory, RAG, agent, validation,
or conversation logic yet.

## Stack

- Python 3.10.12
- uv
- Pydantic v2
- SQLModel
- SQLite
- OpenAI Python SDK
- Pinecone Python SDK

No test directory is required.

## Project Structure

Create:

src/
├── agents/
│   ├── __init__.py
│   ├── memory.py
│   ├── validation.py
│   └── orchestrator.py
│
├── db/
│   ├── __init__.py
│   └── connection.py
│
├── models/
│   ├── __init__.py
│   └── model.py
│
├── repositories/
│   ├── __init__.py
│   └── model.py
│
├── services/
│   ├── __init__.py
│   ├── llm.py
│   └── rag.py
│
├── prompts/
│   ├── __init__.py
│   ├── memory.py
│   └── validation.py
│
├── schemas/
│   ├── __init__.py
│   └── model.py
│
├── config.py
└── main.py

README.md
CLAUDE.md
.env.example
pyproject.toml

## Architecture

### agents/

Contains the application-level AI agents and orchestration.

`memory.py`

Create a boilerplate `MemoryAgent` class.

Eventually this agent will handle:
- deciding whether information is worth remembering
- extracting memories
- identifying related memories
- handling memory conflicts
- updating/superseding memories

For now, only create the class/interface.

`validation.py`

Create a boilerplate `ValidationAgent` class.

Eventually this agent will validate:
- memory consistency
- persona consistency
- generated responses

For now, only create the class/interface.

`orchestrator.py`

Create a boilerplate orchestrator function/class that will eventually
coordinate the overall companion loop.

For now, leave the implementation minimal.

---

### services/

Contains integrations and domain services for external AI/retrieval systems.

`llm.py`

Create an `LLMService` boilerplate around the OpenAI Python SDK.

Define interfaces for:
- generating a normal LLM response
- generating a structured response using a Pydantic model
- accepting a system prompt
- accepting messages
- optionally accepting tools

Keep the implementation minimal. Do not implement the actual application
logic yet.

`rag.py`

Create a `RAGService` boilerplate around Pinecone.

Define interfaces for:
- storing/upserting embeddings
- searching embeddings
- deleting embeddings

Do not implement the actual retrieval pipeline yet.

---

### models/

Contains SQLModel database models.

`model.py`

Create one simple sample SQLModel model to establish the pattern.

For example, a minimal `Memory` model with representative fields such as:

- id
- content
- created_at

This is only boilerplate. Do not fully design the memory architecture yet.

---

### repositories/

Contains database persistence abstractions.

`model.py`

Create a boilerplate repository class, e.g. `MemoryRepository`.

It should establish the pattern for database repositories but does not need
full CRUD/business logic yet.

Do not put OpenAI or Pinecone logic here.

---

### db/

`connection.py`

Create basic SQLite + SQLModel database connection/session scaffolding.

Keep this responsible only for database connectivity and session creation.

---

### schemas/

Contains Pydantic models used for application/LLM input and output contracts.

`model.py`

Create a few simple boilerplate Pydantic models to establish the pattern.

Do not fully implement the eventual memory or validation schemas yet.

---

### prompts/

`memory.py`

Create:

`build_memory_prompt(context: dict) -> str`

Return placeholder prompt content for now.

`validation.py`

Create:

`build_validation_prompt(context: dict) -> str`

Return placeholder prompt content for now.

---

### config.py

Use Pydantic Settings for environment-based configuration.

Include:

- OPENAI_API_KEY
- OPENAI_MODEL
- PINECONE_API_KEY
- PINECONE_INDEX
- DATABASE_URL

Do not hardcode credentials.

---

### main.py

Create a minimal application entry point.

No actual chat loop is required yet.

---

## Dependency Direction

Keep the architecture conceptually clean:

agents
    ↓
services / repositories
    ↓
external systems / database

Agents may use:
- services
- repositories
- prompts
- schemas

Services handle external integrations such as OpenAI and Pinecone.

Repositories handle database persistence.

Models define database entities.

Schemas define Pydantic contracts.

Prompts contain prompt construction.

Do not create unnecessary abstractions or base classes.

## Project Configuration

Use `uv` to initialize the project and manage dependencies.

Set the Python requirement to:

`>=3.10,<3.11`

The scaffold must be compatible with Python 3.10.12.

Add appropriate dependencies for:

- pydantic
- pydantic-settings
- sqlmodel
- openai
- pinecone
- python-dotenv

Keep the dependency list minimal.

## Important

This is a SCAFFOLD ONLY.

Do not:
- implement the memory algorithm
- implement conflict resolution
- implement vector retrieval
- implement agent reasoning
- implement validation logic
- build a CLI chat experience
- create tests
- add frontend/UI
- add unnecessary infrastructure

The purpose of this step is to establish a clean filesystem,
dependency setup, and interfaces that we will implement incrementally.

# AI Companion — Memory & Evaluation

An AI companion with persistent memory: it extracts facts from
conversation, remembers them across turns, resolves contradictions
(supersession), retrieves only what's relevant to the current session, and
validates its own responses against persona and memory consistency before
they're shown to the user.

## Status

Fully implemented end to end: terminal chat (`src/main.py`), the
Companion → Validation → Memory pipeline (`Orchestrator.handle_turn`),
memory extraction + resolution/supersession, and a scripted evaluation
harness (`src/eval/harness.py`) that exercises the whole thing against a
real 15-turn conversation. Built spec-first — see [`.specs/`](#specs) for
the numbered design docs, in the order the system was actually built.

## Stack

- Python 3.10
- [uv](https://docs.astral.sh/uv/) for dependency management
- Pydantic v2 / Pydantic Settings
- SQLModel + SQLite (conversation history, sessions)
- OpenAI Python SDK, pointed at **Groq's** OpenAI-compatible endpoint (not
  OpenAI itself — see [Design decisions](#design-decisions))
- Pinecone (vector storage + hosted embedding inference) for long-term memory

## Setup

```bash
uv sync
cp .env.example .env   # fill in GROQ_API_KEY, PINECONE_API_KEY, PINECONE_INDEX
uv run python src/main.py
```

### Environment variables (`.env`)

| Variable | Default | Purpose |
|---|---|---|
| `GROQ_API_KEY` | — | Groq API key (LLM calls go through Groq, via the OpenAI SDK's `base_url` override) |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | Chat model for all three agents |
| `PINECONE_API_KEY` | — | Pinecone API key |
| `PINECONE_INDEX` | — | Pinecone index name (vector storage for memories) |
| `PINECONE_EMBEDDING_MODEL` | `multilingual-e5-large` | Pinecone-hosted embedding model |
| `MEMORY_RESOLUTION_TOP_K` | `8` | Candidate memories retrieved per fact before resolution |
| `MEMORY_SIMILARITY_THRESHOLD` | `0.75` | Minimum similarity for a retrieved memory to be considered a resolution candidate at all |
| `LLM_CALL_DELAY_SECONDS` | `1.0` | Flat delay between LLM calls in the eval harness and in `MemoryAgent.store()`'s per-fact loop, to stay under rate limits |
| `DATABASE_URL` | `sqlite:///./app.db` | SQLite connection string |

## Running it

**Interactive chat** (persona loaded from `persona.txt`, one session per run):
```bash
uv run python src/main.py
```

**Evaluation harness** (scripted 15-turn conversation, real APIs, PASS/FAIL report):
```bash
uv run python src/eval/harness.py
```
Writes the full transcript + evaluation summary to
`evaluation_runs/<timestamp>_companion_case.txt` (gitignored — local
artifacts only) and prints it live to the terminal. Cleans up everything
it created (DB rows + Pinecone vectors) when it finishes, even on failure.
See [`.specs/009`](.specs/009-companion-evaluation-harness.md) for exactly
what it tests and how.

## Project structure

```
.
├── .specs/                     # numbered design specs, written before each feature (001–009)
├── persona.txt                 # the companion's persona for interactive chat (src/main.py)
├── src/
│   ├── main.py                 # terminal chat entrypoint
│   ├── config.py                # Settings (Pydantic Settings, env-based)
│   ├── agents/                 # LLM-driven reasoning — the only layer that "decides"
│   │   ├── orchestrator.py     #   Orchestrator.handle_turn: coordinates one full turn
│   │   ├── companion.py        #   CompanionAgent: generates the reply
│   │   ├── validation.py       #   ValidationAgent: checks the reply before it's shown
│   │   └── memory.py           #   MemoryAgent: extracts facts, resolves conflicts
│   ├── prompts/                # prompt-building functions + their *ContextModel inputs
│   │   ├── companion.py
│   │   ├── validation.py
│   │   └── memory.py           #   also builds the memory-resolution prompt
│   ├── schemas/                # Pydantic contracts — LLM structured output + API I/O
│   │   ├── companion.py        #   CompanionResponse
│   │   ├── validation.py       #   ValidationResponse
│   │   ├── memory.py           #   MemoryFact, MemoryResponse, MemoryRecord,
│   │   │                       #   MemoryRelation, ResolutionResponse
│   │   ├── chat.py             #   ChatCreate/ChatResponse (API-layer contracts; unused
│   │   │                       #   by main.py/harness, no API routes exist yet)
│   │   └── session.py          #   SessionCreate/SessionResponse (same, unused for now)
│   ├── models/                 # SQLModel database entities
│   │   ├── chat.py             #   Chat, ChatSource enum (user/agent/validator)
│   │   └── session.py          #   Session
│   ├── repositories/           # DB persistence only — never talks to OpenAI/Pinecone
│   │   ├── chat.py             #   ChatRepository (create/get/delete)
│   │   └── session.py          #   SessionRepository (create/get/update/delete)
│   ├── services/                # the only layer allowed to call external APIs
│   │   ├── llm.py              #   LLMService: wraps the OpenAI SDK (→ Groq)
│   │   └── rag.py              #   RAGService: wraps Pinecone (upsert/search/
│   │                           #   update_metadata/delete/embed)
│   ├── db/
│   │   └── connection.py       # SQLite engine + init_db()/get_session()
│   └── eval/
│       └── harness.py          # scripted 15-turn evaluation run (see below)
└── evaluation_runs/            # gitignored — harness output lands here
```

### Dependency direction

```
agents  →  services / repositories  →  external systems / database
```

`agents/` may use `services/`, `repositories/`, `prompts/`, and `schemas/`.
`services/` are the only code that talks to Groq or Pinecone. `repositories/`
only ever touch the SQLite session. Nothing imports "up" the stack. (See
`CLAUDE.md` for the full convention list this repo was built against.)

## How one turn works

`Orchestrator.handle_turn(q)` ([`src/agents/orchestrator.py`](src/agents/orchestrator.py)):

```
search active memories for this session (RAGService, scoped by session_id + status="active")
retrieve recent conversation history
loop (up to 1 initial + 3 retries):
    Companion generates a reply (persona + memories + conversation [+ regen instructions])
    Validation checks it (memory consistency, persona consistency, unsupported claims, persona drift)
    if valid → break
    else → pass validator's feedback back to Companion as `instructions`, retry
persist ONLY the final validated reply as a Chat row
Memory agent extracts facts from the finished conversation
for each fact: resolve against existing active memories, then persist
return the final reply
```

Two things this deliberately does *not* do, because they caused real bugs
earlier in development and got fixed:
- **Rejected candidate replies and validator feedback are never persisted
  as chat history.** Only the final, validated reply becomes a `Chat` row;
  the validator's rejection reason travels as an in-memory `instructions`
  string, not a fake conversation turn.
- **Recent conversation is returned in true chronological order**, not
  reversed — `ChatRepository.get_recent_for_session` queries newest-first
  (for an efficient `LIMIT`) then reverses the result before returning it.

## Memory: extraction, retrieval, resolution

- **Extraction** (`MemoryAgent.query`): given recent conversation, the LLM
  identifies discrete, user-supported facts worth remembering — nothing is
  invented, and companion-only statements or small talk are skipped.
- **Retrieval**: `RAGService.search(q, session_id=..., status="active")` —
  every retrieval is scoped to the current session and to memories that
  haven't been superseded.
- **Resolution** (`MemoryAgent.resolve` + `store`, per
  [`.specs/008`](.specs/008-memory-resolution.md)): before a new fact is
  stored, `store()` retrieves the current session's active memories
  similar enough to the new fact (`MEMORY_SIMILARITY_THRESHOLD`) and asks
  the LLM, in one call per fact, how the new fact relates to each
  candidate: `supersede` (candidate is no longer true — e.g. a job
  change), `update` (candidate is still true, just refreshed), or nothing
  at all. The LLM makes that judgment call; applying it — flipping
  `status`/`superseded_by` in Pinecone via `RAGService.update_metadata`,
  or skipping the upsert entirely if the new fact is a `duplicate`/
  `merged` — is deterministic code with no reasoning of its own.
- Old (superseded) vectors are never deleted or have their embeddings
  overwritten — only their metadata changes. Confidence/importance scores
  are never touched by resolution, only by extraction.

## Evaluation harness

`src/eval/harness.py` runs a fixed 15-turn conversation (the "Maya" case
study) against the real `Orchestrator`, testing memory extraction, noise
resistance (small talk shouldn't create memories), semantic retrieval,
contradiction/supersession (a job change from Microsoft to Adobe), and
persona consistency — full scenario and pass/fail criteria in
[`.specs/009`](.specs/009-companion-evaluation-harness.md).

It wraps `RAGService.upsert`/`search`/`update_metadata` on its own
instance (never touching `src/`) to log exactly what happened on each
turn, so four of the six evaluation categories are exact reads of that log
rather than heuristic re-searches after the fact; the other two (does the
final reply say "Adobe" and not "Microsoft", does it stay in character)
are necessarily text checks on what the LLM actually said. Everything the
run creates — chats, the session, memory vectors — is deleted afterward,
always, even if a turn fails partway through.

## Specs

Built spec-first: each `.specs/NNN-*.md` file was written before its
corresponding code, and later specs build on earlier ones.

| Spec | What it added |
|---|---|
| [001](.specs/001-scaffold.md) | Initial scaffold: dependency direction, folder layout, boilerplate interfaces |
| [002](.specs/002-session-chat-models.md) | `Session`/`Chat` SQLModel entities + repositories |
| [003](.specs/003-prompt-context-models.md) | `*ContextModel` pattern for validating prompt inputs |
| [004](.specs/004-populate-llm-rag-services.md) | Real `LLMService`/`RAGService` implementations (OpenAI SDK, Pinecone) |
| [005](.specs/005-validation-agent.md) | `ValidationAgent` |
| [006](.specs/006-memory-agent.md) | `MemoryAgent` (extraction only, no persistence) |
| [007](.specs/007-companion-agent.md) | `CompanionAgent` |
| [008](.specs/008-memory-resolution.md) | Memory resolution / supersession layer |
| [009](.specs/009-companion-evaluation-harness.md) | The evaluation harness |

## Design decisions

A few choices worth knowing the reasoning behind:

- **Groq instead of OpenAI for the LLM.** `LLMService` still uses the
  `openai` Python package, just pointed at Groq's OpenAI-compatible
  endpoint (`base_url="https://api.groq.com/openai/v1"`) — no new
  dependency, same `generate(system_prompt, response_model)` interface.
- **Memory resolution lives on `MemoryAgent`, not the Orchestrator.**
  `.specs/008` deliberately keeps the LLM judgment call (`resolve()`) and
  its deterministic application (`_apply_relations()`) both inside
  `MemoryAgent`, following the precedent `store()` already set (it already
  called `RAGService.upsert` directly) — this also meant no changes were
  needed to `Orchestrator.handle_turn`'s call site.
- **The validation retry loop never leaks internal state into
  conversation history.** Rejected replies and validator feedback exist
  only as local variables during a turn; only the final valid reply
  becomes persisted `Chat` history that `MemoryAgent` or future turns ever
  see.
- **The eval harness observes via method-wrapping, not mocking.** Rather
  than faking Pinecone calls or threading extra return values through
  `Orchestrator`/`MemoryAgent` (which would mean changing production code
  just to serve test cleanup), the harness wraps three `RAGService`
  methods on its own instance to log calls transparently — the real
  Orchestrator → agent → service flow is never bypassed.

## Known limitations

- Two of the harness's six evaluation categories (long-range consistency,
  persona consistency) are text heuristics on the LLM's actual reply, not
  exact checks — flagged in `.specs/009` as worth a human skim of the
  transcript rather than trusting a green checkmark alone.
- `schemas/chat.py` and `schemas/session.py` define API-layer request/
  response contracts, but no HTTP API exists yet — only the terminal chat
  and the harness consume this system directly.
- This is an assignment-scoped implementation: no test suite, no CI, no
  production-scale infrastructure (retry/backoff, connection pooling,
  etc.) — by design, per `CLAUDE.md`'s scope and the harness spec's own
  "not a production evaluation platform" note.

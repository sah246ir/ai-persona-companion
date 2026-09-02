# Memory Resolution (Supersession/Update) Layer

File: `agents/memory.py`

## Purpose

When a new `MemoryFact` is extracted, decide how it relates to existing
active memories for the session — create a new memory, supersede old ones,
update related ones, or treat it as a duplicate — before it's persisted to
Pinecone. This closes the gap between "extract facts" (`.specs/006`) and
"memory stays internally consistent over time" (not yet implemented).

`.specs/006-memory-agent.md` (Conventions) deliberately stripped conflict
resolution out of `MemoryAgent`, deferring "searching existing memories,
detecting conflicts, superseding old memories" to be "handled outside the
agent." This spec reverses that deferral, now that `RAGService` and
`MemoryAgent.store()` exist to support it — `resolve_conflicts`/
`update_memory` from the original `.specs/001-scaffold.md` stub effectively
return here in a different shape.

## Dependencies

- `LLMService`
- `RAGService`

## Where this fits in the existing pipeline

No new agent class. This is a new method on `MemoryAgent` (`resolve()`),
plus deterministic apply logic that lives alongside the existing `store()`
flow — same boundary rule as the rest of the system: **agents decide**,
**code executes**.

```text
MemoryAgent.store() [existing]        MemoryAgent.resolve() [new]
        |                                       |
        v                                       v
 MemoryResponse.facts[]  --for each fact-->  resolution step  -->  _apply_relations()  -->  Pinecone upsert/metadata update
```

The resolution step is inserted inside the existing per-fact loop in
`store()`, before the final upsert for that fact — no separate pipeline
stage is added in the Orchestrator.

## `schemas/memory.py`

Add `MemoryRelation`, a Pydantic model with:

- `memory_id: str`
- `action: Literal["supersede", "update", "ignore"]`
- `reasoning: str` — short; for logs/debugging only, never persisted as a
  chat message.

Add `ResolutionResponse`, a Pydantic model with:

- `new_fact_status: Literal["active", "duplicate", "merged"]`
- `relations: list[MemoryRelation]`

`relations` omits unaffected candidates entirely rather than returning an
explicit `"ignore"` for every candidate — keeps the response small and the
prompt honest about "silence = untouched."

`action` semantics:

- `supersede` — the old fact is no longer true (e.g. "works at Microsoft" →
  "works at Adobe"). The old memory becomes `inactive`.
- `update` — the old fact is still true, but the new fact adds nuance
  without contradicting it (e.g. "still consults for Google" stays active,
  just gets a fresh `updated_at`). The old memory stays `active`.

There is deliberately no third "merge into candidate" action for
candidates — that direction is handled by `new_fact_status`
(`"duplicate"`/`"merged"`) instead, to keep `action` unambiguous.

## `agents/memory.py`

### `resolve(new_fact: MemoryFact, candidates: list[MemoryRecord]) -> ResolutionResponse`

1. If `candidates` is empty, skip the LLM call entirely and return
   `ResolutionResponse(new_fact_status="active", relations=[])`.
2. Otherwise build the resolution prompt via `build_resolution_prompt`
   (`prompts/memory.py`), passing the new fact and all candidates together
   so the model can reason about their relationships to each other — one
   LLM call per new fact, not one call per candidate.
3. Call `LLMService.generate` with `ResolutionResponse` as the
   `response_model`.
4. Return the resulting `ResolutionResponse`.

### Candidate retrieval (deterministic, inside `store()`)

```python
matches = rag_service.search(
    fact.fact,
    top_k=settings.MEMORY_RESOLUTION_TOP_K,
    session_id=session_id,
    status="active",
)
candidates = [
    MemoryRecord(**m["metadata"])
    for m in matches
    if m["score"] >= settings.MEMORY_SIMILARITY_THRESHOLD
]
```

Scope: current session, `status == "active"` only. Superseded/inactive
memories are never candidates. `top_k` and the similarity threshold are
config constants (`config.py`), not hardcoded inline. Below-threshold or
empty results mean `resolve()` is called with an empty candidate list,
which itself short-circuits without an LLM call.

### `_apply_relations(relations, new_memory_id, now)` (deterministic — private method, no reasoning)

```python
for rel in relations:
    if rel.action == "supersede":
        rag_service.update_metadata(rel.memory_id, {
            "status": "inactive",
            "superseded_by": new_memory_id,
            "updated_at": now,
        })
    elif rel.action == "update":
        rag_service.update_metadata(rel.memory_id, {"updated_at": now})
    # "ignore" (or anything unexpected) is a no-op — no branch needed
```

`store()` then upserts the new record's embedding as usual, unless
`resolution.new_fact_status` is `"duplicate"` or `"merged"`, in which case
no new vector is created for that fact.

## `services/rag.py`

Add `update_metadata(id: str, metadata: dict[str, Any]) -> None`, wrapping
the Pinecone SDK's `index.update(id=..., set_metadata=...)` to patch an
existing vector's metadata in place without touching its embedding values.

## `config.py`

Add:

- `MEMORY_RESOLUTION_TOP_K: int` — how many candidate memories to retrieve
  per fact before resolution.
- `MEMORY_SIMILARITY_THRESHOLD: float` — minimum similarity score for a
  retrieved memory to be considered a resolution candidate at all.

Mirror both in `.env.example`, per the convention `.specs/004` establishes.

## Invariants to preserve

- Confidence scores are never mutated by resolution. Only `status`,
  `superseded_by`, and `updated_at` change. Confidence answers "how sure
  are we this fact is/was true"; `status` answers "is it currently in
  effect" — these stay independent per the existing design.
- No embeddings are overwritten or deleted. Old vectors remain in Pinecone
  with `status: inactive`; only new vectors are ever inserted.
- Reasoning about temporal language is semantic, not keyword-based. "Used
  to work at X, now at Y" ⇒ supersede. "Works at X and also consults for
  Y" ⇒ both stay active. This distinction is the LLM's job inside
  `resolve()`, not a regex/keyword heuristic in application code.
- Resolution never touches chat history. `reasoning` strings are for logs
  only — same rule as validator feedback: internal reasoning never becomes
  a persisted chat message.

## Acceptance criteria

- Given a new fact with no semantically related active memories, it's
  upserted as active with no LLM resolution call made.
- Given a new fact that contradicts exactly one active memory (e.g.
  employer change), that memory is marked inactive with `superseded_by`
  set to the new memory's id; the new memory is active.
- Given a new fact where multiple existing memories are related but only
  some are actually contradicted (the Google/Microsoft/Adobe case), only
  the contradicted ones become inactive; unrelated or merely-nuanced ones
  stay active, with unaffected ones untouched entirely (not present in
  `relations`).
- Given a new fact that is a near-duplicate of an existing active memory,
  no new vector is created (`new_fact_status: "duplicate"`).
- No test case ever results in a confidence score being changed by this
  flow.
- Retrieval for `resolve()` candidates is always scoped to `status ==
  "active"` and the current session — inactive/superseded memories are
  never re-surfaced as candidates for future resolution.

## Out of scope

- No new agent class (`ConflictAgent`, `SupersessionAgent`, etc.) — stays a
  `MemoryAgent` method.
- No changes to `CompanionAgent`, `ValidationAgent`, or the validation
  retry flow.
- No changes to extraction (`MemoryAgent.query()`) beyond inserting the
  resolution call into the existing per-fact loop in `store()`.

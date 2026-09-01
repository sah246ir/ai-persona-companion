# Memory Agent

File: `agents/memory.py`

Create a `MemoryAgent` class responsible for analyzing recent conversation
history and identifying user information that should be persisted as
long-term memory.

## Dependencies

- `LLMService`

## `schemas/memory.py`

Add `MemoryResponse`, a Pydantic model with:

- `has_memory: bool`
- `facts: list[MemoryFact]`

Add `MemoryFact`, a Pydantic model with:

- `fact: str`
- `message_id: int`
- `type`
- `importance_score`
- `confidence_score`

`fact` contains a concise statement representing information about the user
that may be useful as long-term memory.

`message_id` identifies the user message from which the fact was extracted.

`type` classifies the memory as one of:

- `preference`
- `personal_info`
- `goal`
- `relationship`
- `context`
- `other`

`importance_score` represents how valuable the fact is to retain as
long-term memory, from 0 to 1.

`confidence_score` represents how confident the agent is that the extracted
fact is accurate, from 0 to 1.

`has_memory` indicates whether the conversation contains any information
worth storing as long-term memory. If `has_memory` is `false`, `facts`
should be an empty list.

## `agents/memory.py`

`MemoryAgent(llm_service: LLMService)`.

### `query(context: dict) -> MemoryResponse`

1. Build the memory prompt using `build_memory_prompt` from the memory
   prompt builder (`prompts/memory.py`).
2. The prompt builder validates `context` against
   `MemoryPromptContextModel`, containing the recent `conversation`.
3. Call `LLMService` to query the LLM.
4. Pass `MemoryResponse` as the `response_model` to `LLMService`.
5. Return the resulting `MemoryResponse`.

## Conventions

`query` is the sole public method on `MemoryAgent`.

The Memory Agent is responsible only for **memory identification and
extraction**. It does not directly persist, update, or delete memories.

The Memory Agent should analyze the recent conversation, including both
user messages and companion responses, but should primarily extract facts
that are explicitly supported by information provided by the user.

The agent should not treat normal conversational filler, temporary
statements, or information about the companion itself as user memory.

Memory persistence and lifecycle operations such as searching existing
memories, detecting conflicts, superseding old memories, and writing to
Pinecone are handled outside the agent.

`MemoryResponse` and `MemoryFact` live in `schemas/`, since they define the
structured LLM output contract — the same distinction
`.specs/003-prompt-context-models.md` draws between `*ContextModel`s (in
`prompts/`) and application/LLM I/O contracts (in `schemas/`).

`MemoryPromptContextModel` remains in `prompts/memory.py` as the validation
model for prompt input. No additional context model is introduced; the
existing `MemoryPromptContextModel` (previously also carrying
`existing_memories`, used for conflict handling) is trimmed to just
`conversation`, since conflict handling is out of scope for this agent.

This replaces the earlier `MemoryAgent` stub from `.specs/001-scaffold.md`
(`should_remember` / `extract_memories` / `find_related` /
`resolve_conflicts` / `update_memory`, depending on `RAGService` and a
`MemoryRepository` that was never implemented) with the single `query`
method described above, mirroring the design `ValidationAgent`
(`.specs/005-validation-agent.md`) already established.

# Companion Agent

File: `agents/companion.py`

Create a `CompanionAgent` class responsible for generating the companion's
response to the user, consistent with the persona and relevant memory
context.

## Dependencies

- `LLMService`

## `schemas/companion.py`

Add `CompanionResponse`, a Pydantic model with:

- `message: str`

`message` is the companion's natural-language reply to the user.

## `agents/companion.py`

`CompanionAgent(llm_service: LLMService)`.

### `query(context: dict) -> CompanionResponse`

1. Build the companion prompt using `build_companion_prompt` from the
   companion prompt builder (`prompts/companion.py`), which validates
   `context` against `CompanionPromptContextModel` (`persona`, `memories`,
   `conversation`).
2. Call `LLMService` to query the LLM.
3. Pass `CompanionResponse` as the `response_model` to `LLMService`.
4. Return the resulting `CompanionResponse`.

## Conventions

`query` is the sole public method on `CompanionAgent`, matching
`ValidationAgent` (`.specs/005-validation-agent.md`) and `MemoryAgent`
(`.specs/006-memory-agent.md`).

`CompanionResponse` lives in `schemas/`, not next to the prompt builder,
for the same reason `ValidationResponse` and `MemoryResponse` do: it is a
Pydantic contract for LLM *output*, while `CompanionPromptContextModel` (in
`prompts/`) validates prompt *input* — the distinction
`.specs/003-prompt-context-models.md` draws.

`LLMService.generate` always requires a `response_model`; there is no plain
text-completion path, so even a single-field reply needs a minimal
structured schema rather than returning a bare string.

No new context model is introduced — `CompanionPromptContextModel`
(`.specs/003-prompt-context-models.md`) already validates the `context`
dict `query` receives, via `build_companion_prompt`.

Unlike `MemoryAgent`/`ValidationAgent`, no boilerplate stub for
`CompanionAgent` existed in `.specs/001-scaffold.md` — this introduces the
agent from scratch, reusing the prompt builder already added in
`.specs/003-prompt-context-models.md`.

Wiring `CompanionAgent` into `Orchestrator` is out of scope here.

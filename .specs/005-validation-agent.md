# Validation Agent

File: `agents/validation.py`

Create a `ValidationAgent` class responsible for evaluating whether a
generated companion response is consistent with the provided context.

## Dependencies

- `LLMService`

## `schemas/validation.py`

Add `ValidationResponse`, a Pydantic model with:

- `is_valid: bool`
- `memory_score`
- `persona_score`
- `unsupported_claims_score`
- `persona_drift_score`
- `description: str`

The scores evaluate memory consistency, persona consistency, unsupported
claims, and persona drift, respectively. `description` explains any detected
issues or inconsistencies.

## `agents/validation.py`

`ValidationAgent(llm_service: LLMService)`.

### `query(context: dict) -> ValidationResponse`

1. Build the validation prompt using `build_validation_prompt` from the
   validation prompt builder (`prompts/validation.py`), which validates
   `context` against `ValidationPromptContextModel` (`persona`, `memories`,
   `conversation`, `response`).
2. Call `LLMService` to query the LLM.
3. Pass `ValidationResponse` as the `response_model` to `LLMService`.
4. Return the resulting `ValidationResponse`.

## Conventions

`query` is the sole public method on `ValidationAgent`, replacing the three
`validate_memory_consistency` / `validate_persona_consistency` /
`validate_response` stubs from `.specs/001-scaffold.md`. Those predated the
actual validation prompt; `build_validation_prompt` already evaluates memory
consistency, persona consistency, unsupported claims, and persona drift
together in one LLM call, so one method mirrors that design instead of
splitting it into calls that don't match the prompt.

`ValidationResponse` lives in `schemas/`, not next to the prompt builder,
since it is a Pydantic contract for LLM *output* rather than prompt-input
validation — the same distinction `.specs/003-prompt-context-models.md`
draws between `*ContextModel`s (in `prompts/`) and application/LLM I/O
contracts (in `schemas/`).

No new context model is introduced — `ValidationPromptContextModel`
(`.specs/003-prompt-context-models.md`) already validates the `context` dict
`query` receives, via `build_validation_prompt`.

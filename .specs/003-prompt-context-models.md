# Prompt Context Validation

Validate the `context` dict passed into each prompt builder in `prompts/`
before it is used to format the prompt string.

## `prompts/companion.py`

Add `CompanionPromptContextModel`, a Pydantic model with:

- `persona`
- `memories`
- `conversation`

`build_companion_prompt(context: dict)` should validate `context` against
this model before building the prompt.

## `prompts/memory.py`

Add `MemoryPromptContextModel`, a Pydantic model with:

- `conversation`
- `existing_memories`

`build_memory_prompt(context: dict)` should validate `context` against this
model before building the prompt.

## `prompts/validation.py`

Add `ValidationPromptContextModel`, a Pydantic model with:

- `persona`
- `memories`
- `conversation`
- `response`

`build_validation_prompt(context: dict)` should validate `context` against
this model before building the prompt.

## Conventions

Each context model lives in the same file as the prompt builder that uses
it, not in `schemas/`, since it validates internal prompt-construction input
rather than an application/LLM I/O contract.

Model class names end in `Model` (e.g. `CompanionPromptContextModel`) to
distinguish them from any future non-Pydantic context types in `prompts/`.

A missing or wrong-typed key in `context` should raise a Pydantic
`ValidationError` instead of failing with a `KeyError` during string
formatting.

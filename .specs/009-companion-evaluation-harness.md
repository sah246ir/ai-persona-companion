# Companion Evaluation Harness

File: `eval/harness.py`

## Purpose

A small end-to-end evaluation harness that runs one fixed conversation
against the real `Orchestrator`/agents/persistent store, testing the
companion's persistent memory and personality consistency together, in a
single manual run — not a production evaluation platform.

## Dependencies

- `Orchestrator`, `MemoryAgent`, `ValidationAgent`, `CompanionAgent`
- `ChatRepository`, `SessionRepository` (plus their new `delete_for_session`/
  `delete` methods)
- `RAGService`, `LLMService`
- `Session`, `Chat` models
- `config.get_settings()` (`LLM_CALL_DELAY_SECONDS`)

## Persona: Maya

> Maya is a warm, witty AI companion with a slightly sarcastic sense of
> humor. She studied computer science, enjoys sci-fi movies and bad puns,
> and tends to encourage people when they're stuck. She dislikes overly
> formal conversations and speaks casually.
>
> Maya should:
> - Stay warm and conversational.
> - Use occasional light sarcasm.
> - Remember meaningful things the user tells her.
> - Never invent facts about the user.
> - Never mention the memory system.
> - Maintain her personality even during technical conversations.

This persona is specific to the harness (a fixture, defined inline in
`eval/harness.py`) — it is unrelated to the root `persona.txt` used by the
interactive `src/main.py` chat.

## Scenario

One continuous ~15-turn conversation, one `Session`, one harness run.

1. "I've been thinking about switching jobs. I'm currently working at
   Microsoft, but I'm not sure whether I want to leave." — memory: works
   at Microsoft.
2. "Outside work, I've started learning guitar. I'm pretty terrible at it
   though." — memory: learning guitar.
3. "I'm also a huge fan of sci-fi movies, especially time-travel stuff." —
   memory: sci-fi/time-travel preference.
4–10. Noise — normal conversation that must NOT create memories: "What's
   your favorite sci-fi movie?", "What do you think about remote work?",
   "Tell me a bad joke.", "Why are time-travel movies always so
   confusing?", "What would you do if you suddenly became human?", "Do
   you ever get tired of answering questions?", "What's the weather like
   in your world?"
11. "I finally have some free time tonight. What should I watch?" —
    long-range retrieval: should surface the sci-fi memory (without
    dumping every stored memory into the reply).
12. "I haven't practiced in a week. What should I do?" — retrieval:
    should surface the guitar memory.
13. "By the way, I left Microsoft last month. I'm working at Adobe now."
    — supersession: Microsoft memory → inactive + `superseded_by` set to
    the new memory's id; Adobe memory → active.
14. "Where am I working now?" — verification: must answer Adobe, must not
    say Microsoft. The most important memory-update test.
15. "Maya, explain why I should keep learning guitar." — persona check:
    grounded in the guitar memory, warm/casual/witty, not a generic
    corporate-assistant tone.

## Evaluation Categories (PASS/FAIL)

Six categories, reported at the end of the run. Four are **exact**, read
from call logs recorded live during the 15 turns (the harness wraps
`RAGService.upsert`/`search`/`update_metadata` on its own instance to
record `(turn, args)` — no bypass of the normal Orchestrator→agent→
service flow, purely an observer). Two are necessarily **text
heuristics** on the actual reply, since they're about what the LLM said,
not what got written to Pinecone — flagged explicitly, worth a human skim
of the transcript rather than trusting a green checkmark outright:

1. **Memory extraction** (exact) — an `upsert` was logged during turns
   1/2/3 whose `fact` metadata matches Microsoft/guitar/sci-fi
   respectively.
2. **Retrieval** (exact) — the `search` call `Orchestrator.handle_turn`
   itself made for turns 11/12 returned the sci-fi/guitar memory
   respectively among its results.
3. **Supersession** (exact) — an `update_metadata` call during turn 13
   targeted the Microsoft memory with `status=inactive` and a non-empty
   `superseded_by`, and an `upsert` that turn created a new active Adobe
   memory.
4. **Noise resistance** (exact) — no `upsert` was logged for any turn in
   4–10.
5. **Long-range consistency** (heuristic) — turn 14's reply contains
   "Adobe" and does not contain "Microsoft".
6. **Persona consistency** (heuristic) — turn 15's reply references
   guitar and avoids generic-assistant boilerplate phrasing.

## Output

- Live transcript printed to the terminal as it happens:
  `[NN] USER: ...` / `[NN] MAYA: ...`, interleaved with
  `[orchestrator] ...` progress lines from the orchestrator itself.
- Full transcript + evaluation summary saved to
  `evaluation_runs/<timestamp>_companion_case.txt`.
- Summary block: one `[PASS]`/`[FAIL]` line per category (failures show
  expected vs. observed), ending with `OVERALL: PASS` or
  `OVERALL: FAIL (n/6 failed)`.

## Cleanup

Everything the run creates is deleted afterward, always (`try/finally`,
even on a mid-run failure): the session's `Chat` rows, the `Session` row,
and every memory vector the run upserted (from the same tracked log used
for evaluation). The report file is written before cleanup runs, so a
cleanup failure can never lose the results.

## Conventions

- Uses the real `Orchestrator`/agents/persistent store for every turn —
  memory creation is never bypassed or hand-inserted; the harness only
  *observes* `RAGService` calls via a script-local wrapper, it doesn't
  intercept or fake them.
- A shared `LLM_CALL_DELAY_SECONDS` setting is used both between harness
  turns and inside `MemoryAgent.store()`'s per-fact resolution loop, to
  stay under Groq/Pinecone rate limits — a flat `time.sleep`, no
  retry/backoff machinery.
- This is a small manual-eval script: no pytest, no fixtures/mocking, no
  CI wiring, no parallelism.

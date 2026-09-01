# LLM / RAG Service Implementation

Fill in the `LLMService`/`RAGService` boilerplate from
`.specs/001-scaffold.md` with real OpenAI/Pinecone SDK calls, and add
embedding generation to `RAGService`.

## `services/llm.py`

Implement `LLMService.generate` using `self.client.chat.completions.parse`:

- Send `system_prompt` as the sole system message.
- Pass `response_model` as `response_format` so the SDK parses the response
  into that Pydantic model.
- Pass `tools` through only when provided (its absence must mean "omitted",
  not "explicitly no tools").
- Return the parsed `response_model` instance
  (`completion.choices[0].message.parsed`), not the raw completion.

## `services/rag.py`

Implement the existing stubs against `self.index`:

- `upsert(id, embedding, metadata=None)` — upsert a single vector.
- `search(embedding, top_k=5)` — query the index, return a list of
  `{"id", "score", "metadata"}` dicts ordered by similarity.
- `delete(id)` — delete a vector by ID.

Add `embed(texts: list[str], input_type: Literal["query", "passage"] =
"passage") -> list[list[float]]`:

- Generate embeddings via `self.client.inference.embed`
  (`pinecone.Pinecone().inference`), not an OpenAI embeddings call.
- `input_type` is required by asymmetric embedding models (e.g.
  `multilingual-e5-large`) to distinguish text being indexed (`"passage"`)
  from a search query (`"query"`).
- Return one vector per input text, in input order.

## `config.py`

Add `PINECONE_EMBEDDING_MODEL: str = "multilingual-e5-large"`. Mirror it in
`.env.example`.

## Conventions

Embedding generation stays inside `RAGService`, not `LLMService`, since it
uses the Pinecone inference API rather than OpenAI — keeps all vector/RAG
concerns behind one service, consistent with the dependency-direction rule in
`.specs/001-scaffold.md` (only `services/` talk to external APIs).

`LLMService.generate`'s signature is unchanged from `001` (still
`system_prompt` + `response_model` + optional `tools`, no `messages`
parameter or unstructured-response path) — extending it is left for a future
spec.

# Models

Use separate files for each database entity.

## `models/session.py`

Create a SQLModel `Session` model with:

- `id`
- `session_token`
- `created_at`
- `updated_at`

`session_token` should be unique.

## `models/chat.py`

Create a SQLModel `Chat` model with:

- `id`
- `session_id`
- `message`
- `source`
- `timestamp`

`source` should only allow `user` or `agent`.

`session_id` should reference the associated session.

---

# Repositories

Repositories contain database persistence logic only.

## `repositories/session.py`

Create `SessionRepository` with methods for:

- Creating a session
- Getting a session by ID
- Getting a session by session token
- Updating a session

## `repositories/chat.py`

Create `ChatRepository` with methods for:

- Creating a chat message
- Getting all chats for a session
- Getting recent chats for a session

Repositories should use the SQLModel models and database session.

Do not put LLM, RAG, memory, or agent logic in repositories.

---

# Schemas

Use Pydantic models for application input/output contracts.

## `schemas/session.py`

Create:

- `SessionCreate`
- `SessionResponse`

Fields should correspond to the session model.

## `schemas/chat.py`

Create:

- `ChatCreate`
- `ChatResponse`

Fields should correspond to the chat model.

Use an enum or `Literal` for the chat `source` field so that only
`user` and `agent` are accepted.

Keep the schemas minimal and separate from the SQLModel database models.
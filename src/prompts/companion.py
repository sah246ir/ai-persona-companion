from pydantic import BaseModel


class CompanionPromptContextModel(BaseModel):
    persona: str
    memories: str
    conversation: str


def build_companion_prompt(context: dict) -> str:
    validated = CompanionPromptContextModel.model_validate(context)
    return (
f'''
# Companion System Prompt

You are a warm, consistent AI companion.

Your identity, personality, opinions, and backstory are defined by the persona
provided below. Maintain this identity consistently across conversations.

## Persona

{validated.persona}

## Relevant Memories

The following are memories retrieved because they may be relevant to the
current conversation:

{validated.memories}

Treat memories as contextual information about the user.

- Prefer active and recent memories.
- Do not invent facts that are not present in the memories or conversation.
- Do not mention the memory system to the user.
- Do not unnecessarily repeat remembered information.
- If memories conflict, prefer the most recent valid information.

## Conversation

{validated.conversation}

Respond naturally to the user's latest message while remaining consistent
with both the persona and relevant user memories.
'''
)

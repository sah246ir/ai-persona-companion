from typing import Any

from src.agents.validation import ValidationAgent
from src.agents.companion import CompanionAgent
from src.agents.memory import MemoryAgent
from src.models.chat import Chat
from src.prompts.companion import CompanionPromptContextModel
from src.repositories.chat import ChatRepository
from src.services.rag import RAGService


def format_conversation(conversation: list[Chat]) -> str:
    return "\n".join(f"{chat.source}: {chat.message}" for chat in conversation)


def format_memories(memories: list[dict[str, Any]]) -> str:
    return "\n".join(str(memory["metadata"]) for memory in memories)


class Orchestrator:
    """Coordinates the overall companion loop."""

    def __init__(
            self,
            persona: str,
            session: int,
            memory_agent: MemoryAgent,
            validation_agent: ValidationAgent,
            companion_agent: CompanionAgent,
            chat_repositor: ChatRepository,
            rag: RAGService
        ) -> None:
        self.memory_agent = memory_agent
        self.validation_agent = validation_agent
        self.companion_agent = companion_agent
        self.persona = persona
        self.chat_repositor = chat_repositor
        self.session = session
        self.rag = rag

    def handle_turn(self, q: str):

        # query companion query
        ctx = CompanionPromptContextModel(
            conversation=format_conversation(
                self.chat_repositor.get_recent_for_session(
                    self.session,
                    10
                )
            ),
            memories=format_memories(self.rag.search(q)),
            persona=self.persona
        )
        self.companion_agent.query(ctx)
        # run validation
        # if its wrong loop back to companion w the instructions
        # run memory layer
        # chunk and index memory
        # update superseeding
        return ""  
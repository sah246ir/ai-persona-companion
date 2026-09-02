from typing import Any

from agents.validation import ValidationAgent
from agents.companion import CompanionAgent
from agents.memory import MemoryAgent
from models.chat import Chat
from prompts.companion import CompanionPromptContextModel
from prompts.memory import MemoryPromptContextModel
from prompts.validation import ValidationPromptContextModel
from repositories.chat import ChatRepository
from services.rag import RAGService
from models.chat import ChatSource

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
        print("[orchestrator] searching memories...")
        memories = self.rag.search(q, session_id=self.session, status="active")
        chats = self.chat_repositor.get_recent_for_session(
                    self.session,
                    10
                )

        instructions = None
        attempts = 0
        max_retries = 3

        while True:
            companionctx = CompanionPromptContextModel(
                conversation=format_conversation(chats),
                memories=format_memories(memories),
                persona=self.persona,
                instructions=instructions,
            )
            print("[orchestrator] generating response...")
            companionres = self.companion_agent.query(companionctx)

            validationctx = ValidationPromptContextModel(
                conversation=format_conversation(chats),
                memories=format_memories(memories),
                persona=self.persona,
                response=companionres.message
            )
            print("[orchestrator] validating response...")
            validationres = self.validation_agent.query(validationctx)

            if validationres.is_valid:
                break

            attempts += 1
            if attempts > max_retries:
                raise ValueError("validation agent flagged the response multiple times")
            print(f"[orchestrator] validation failed (attempt {attempts}/{max_retries}), regenerating...")
            instructions = validationres.description

        print("[orchestrator] persisting response...")
        chat = self.chat_repositor.create(Chat(
            message=companionres.message,
            session_id=self.session,
            source=ChatSource.agent,
        ))
        chats.append(chat)

        # run memory layer
        memorycts = MemoryPromptContextModel(
            conversation=format_conversation(chats)
        )
        print("[orchestrator] extracting memories...")
        memoryres = self.memory_agent.query(memorycts)

        print("[orchestrator] storing memories...")
        self.memory_agent.store(memoryres,self.session)
        return companionres.message
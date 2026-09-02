from typing import Any

from src.agents.validation import ValidationAgent
from src.agents.companion import CompanionAgent
from src.agents.memory import MemoryAgent
from src.models.chat import Chat
from src.prompts.companion import CompanionPromptContextModel
from src.prompts.memory import MemoryPromptContextModel
from src.prompts.validation import ValidationPromptContextModel
from src.repositories.chat import ChatRepository
from src.services.rag import RAGService
from src.models.chat import ChatSource
from datetime import datetime

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
        memories = self.rag.search(q)
        chats = self.chat_repositor.get_recent_for_session(
                    self.session,
                    10
                )
        # query companion query
        companionctx = CompanionPromptContextModel(
            conversation=format_conversation(chats),
            memories=format_memories(memories),
            persona=self.persona
        )
        companionres = self.companion_agent.query(companionctx)
        chat = self.chat_repositor.create(Chat(
            message=companionres.message,
            session_id=self.session,
            source=ChatSource.agent,
        ))
        chats.append(chat)
        
        # run validation
        # if its wrong loop back to companion w the instructions
        validationctx = ValidationPromptContextModel(
            conversation=format_conversation(chats),
            memories=format_memories(memories),
            persona=self.persona,
            response=companionres.message
        )
        validationres = self.validation_agent.query(validationctx)
        failed = 0

        while not validationres.is_valid:
            failed = failed+1
            if failed==4:
                raise ValueError("validation agent flagged the response multipel times")
            chat = self.chat_repositor.create(Chat(
                        message=validationres.description,
                        session_id=self.session,
                        source=ChatSource.validator,
                    ))
            chats.append(chat)
            companionctx = CompanionPromptContextModel(
                conversation=format_conversation(chats),
                memories=format_memories(memories),
                persona=self.persona
            )
            companionres = self.companion_agent.query(companionctx)
    
            validationctx = ValidationPromptContextModel(
                conversation=format_conversation(chats),
                memories=format_memories(memories),
                persona=self.persona,
                response=companionres.message
            )
            validationres = self.validation_agent.query(validationctx)

        # run memory layer
        memorycts = MemoryPromptContextModel(
            conversation=format_conversation(chats)
        )
        memoryres = self.memory_agent.query(memorycts)
        # chunk and index memory
        # update superseeding
        return ""  
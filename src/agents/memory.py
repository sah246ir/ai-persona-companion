from src.repositories.model import MemoryRepository
from src.services.llm import LLMService
from src.services.rag import RAGService


class MemoryAgent:
    """
    Future responsibilities:
    - deciding whether information is worth remembering
    - extracting memories
    - identifying related memories
    - handling memory conflicts
    - updating/superseding memories
    """

    def __init__(
        self,
        llm_service: LLMService,
        rag_service: RAGService,
        memory_repository: MemoryRepository,
    ) -> None:
        self.llm_service = llm_service
        self.rag_service = rag_service
        self.memory_repository = memory_repository

    def should_remember(self, *args, **kwargs) -> bool:
        raise NotImplementedError

    def extract_memories(self, *args, **kwargs) -> list:
        raise NotImplementedError

    def find_related(self, *args, **kwargs) -> list:
        raise NotImplementedError

    def resolve_conflicts(self, *args, **kwargs) -> None:
        raise NotImplementedError

    def update_memory(self, *args, **kwargs) -> None:
        raise NotImplementedError

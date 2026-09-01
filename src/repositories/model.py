from sqlmodel import Session

from src.models.model import Memory


class MemoryRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, id: int) -> Memory | None:
        raise NotImplementedError

    def list(self) -> list[Memory]:
        raise NotImplementedError

    def add(self, memory: Memory) -> Memory:
        raise NotImplementedError

    def delete(self, id: int) -> None:
        raise NotImplementedError

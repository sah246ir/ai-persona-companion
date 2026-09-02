from pathlib import Path
from uuid import uuid4

from sqlmodel import Session as DBSession

from src.agents.companion import CompanionAgent
from src.agents.memory import MemoryAgent
from src.agents.orchestrator import Orchestrator
from src.agents.validation import ValidationAgent
from src.db.connection import engine, init_db
from src.models.chat import Chat, ChatSource
from src.models.session import Session
from src.repositories.chat import ChatRepository
from src.repositories.session import SessionRepository
from src.services.llm import LLMService
from src.services.rag import RAGService


def main() -> None:
    init_db()
    persona = Path("persona.txt").read_text().strip()

    with DBSession(engine) as db_session:
        session_repo = SessionRepository(db_session)
        chat_repo = ChatRepository(db_session)
        session = session_repo.create(Session(session_token=str(uuid4())))

        llm_service = LLMService()
        rag_service = RAGService()
        orchestrator = Orchestrator(
            persona=persona,
            session=session.id,
            memory_agent=MemoryAgent(llm_service, rag_service),
            validation_agent=ValidationAgent(llm_service),
            companion_agent=CompanionAgent(llm_service),
            chat_repositor=chat_repo,
            rag=rag_service,
        )

        print(f"AI Companion — session {session.id}. Type 'exit' to quit.")
        while True:
            try:
                q = input("You: ").strip()
            except EOFError:
                break
            if not q or q.lower() in ("exit", "quit"):
                break

            chat_repo.create(Chat(message=q, session_id=session.id, source=ChatSource.user))

            try:
                reply = orchestrator.handle_turn(q)
            except ValueError as e:
                print(f"[error] {e}")
                continue

            print(f"Companion: {reply}")


if __name__ == "__main__":
    main()

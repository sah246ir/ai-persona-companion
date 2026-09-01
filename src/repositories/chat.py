from sqlmodel import Session as DBSession, select

from src.models.chat import Chat


class ChatRepository:
    def __init__(self, session: DBSession) -> None:
        self.session = session

    def create(self, chat: Chat) -> Chat:
        self.session.add(chat)
        self.session.commit()
        self.session.refresh(chat)
        return chat

    def get_all_for_session(self, session_id: int) -> list[Chat]:
        statement = (
            select(Chat)
            .where(Chat.session_id == session_id)
            .order_by("timestamp")
        )
        return list(self.session.exec(statement).all())

    def get_recent_for_session(self, session_id: int, limit: int = 20) -> list[Chat]:
        statement = (
            select(Chat)
            .where(Chat.session_id == session_id)
            .order_by(Chat.timestamp.desc())
            .limit(limit)
        )
        return list(self.session.exec(statement).all())

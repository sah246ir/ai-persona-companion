from datetime import datetime

from sqlmodel import Session as DBSession, select

from src.models.session import Session


class SessionRepository:
    def __init__(self, session: DBSession) -> None:
        self.session = session

    def create(self, session: Session) -> Session:
        self.session.add(session)
        self.session.commit()
        self.session.refresh(session)
        return session

    def get_by_id(self, id: int) -> Session | None:
        return self.session.get(Session, id)

    def get_by_token(self, session_token: str) -> Session | None:
        statement = select(Session).where(Session.session_token == session_token)
        return self.session.exec(statement).first()

    def update(self, session: Session) -> Session:
        session.updated_at = datetime.utcnow()
        self.session.add(session)
        self.session.commit()
        self.session.refresh(session)
        return session

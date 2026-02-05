from contextvars import ContextVar
from sqlalchemy.orm import Session

# ContextVar to handle session context safely
db_session: ContextVar[Session] = ContextVar("db_session")


async def get_db() -> Session:
    return db_session.get()

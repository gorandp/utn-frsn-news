from workers import Response, WorkerEntrypoint, Request
from sqlalchemy_cloudflare_d1 import create_engine_from_binding  # type: ignore
from sqlalchemy.orm import sessionmaker, Session


class Default(WorkerEntrypoint):
    async def fetch(self, request: Request):
        engine = create_engine_from_binding(self.env.DB)  # type: ignore
        SessionLocal = sessionmaker(bind=engine)
        with SessionLocal() as session:
            pass  # Main logic would go here
        return Response("Success", status=200)

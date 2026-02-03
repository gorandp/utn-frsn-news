from fastapi import FastAPI, Request, HTTPException, status, Depends
from contextvars import ContextVar
from typing import Annotated
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import select

# from database_models import Base as DbBase
from .. import database_models as models


app = FastAPI()

# ContextVar to handle session context safely
db_session: ContextVar[Session] = ContextVar("db_session")


@app.get("/")
async def root():
    return {"message": "Welcome to the FastAPI application!"}

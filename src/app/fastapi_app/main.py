from fastapi import FastAPI, Request, HTTPException, status, Depends
from typing import Annotated
from sqlalchemy.orm import Session
from sqlalchemy import select

# from database_models import Base as DbBase
from .. import database_models as models
from ..logger import LogWrapper
from .schemas import NewsResponse
from .database import get_db


app = FastAPI()


logger = LogWrapper().logger


@app.get("/")
async def root(req: Request, db: Annotated[Session, Depends(get_db)]):
    return {"message": "Welcome to the FastAPI application!"}


@app.get("/api/news", response_model=list[NewsResponse])
async def get_news(req: Request, db: Annotated[Session, Depends(get_db)]):
    logger.info("Fetching news items from the database")
    try:
        result = db.execute(select(models.News).limit(10))
        news_items = result.scalars().all()
        return [item.__dict__ for item in news_items]
    except Exception as e:
        logger.info(f"Error fetching news: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )

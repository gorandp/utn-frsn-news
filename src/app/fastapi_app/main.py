from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.templating import Jinja2Templates
from typing import Annotated
from sqlalchemy.orm import Session
from sqlalchemy import select
import os

# from database_models import Base as DbBase
from .. import database_models as models
from ..logger import LogWrapper
from .schemas import NewsResponse
from .database import get_db


app = FastAPI()

templates = Jinja2Templates(
    directory=os.path.join(os.path.dirname(__file__), "templates")
)

logger = LogWrapper().logger


@app.get("/", include_in_schema=False)
async def index(
    req: Request,
    db: Annotated[Session, Depends(get_db)],
):
    news_list = (
        db.execute(
            select(models.News).order_by(models.News.origin_created_at.desc()).limit(10)
        )
        .scalars()
        .all()
    )
    return templates.TemplateResponse(
        req,
        "home.html",
        {"news_list": news_list},
    )


@app.get("/news/{news_id}", include_in_schema=False)
async def get_news_item(
    news_id: int,
    req: Request,
    db: Annotated[Session, Depends(get_db)],
):
    news = (
        db.execute(select(models.News).where(models.News.id == news_id))
        .scalars()
        .first()
    )
    return templates.TemplateResponse(
        req,
        "news_detail.html",
        {"news": news},
    )


@app.get("/api/news", response_model=list[NewsResponse])
async def get_news(
    req: Request,
    db: Annotated[Session, Depends(get_db)],
):
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

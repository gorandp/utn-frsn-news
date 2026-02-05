import os
from typing import Annotated
from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime, timedelta, timezone

# from database_models import Base as DbBase
from .. import database_models as models
from ..logger import LogWrapper
from .schemas import NewsResponse, NewsShortResponse, NewsSearchResponse
from .database import get_db


app = FastAPI()

templates = Jinja2Templates(
    directory=os.path.join(os.path.dirname(__file__), "templates")
)

logger = LogWrapper().logger


@app.get("/about", include_in_schema=False)
async def about(
    req: Request,
):
    return templates.TemplateResponse(
        req,
        "about.html",
    )


@app.get("/", include_in_schema=False, name="index")
@app.get("/news", include_in_schema=False, name="news_index")
async def index(req: Request):
    return templates.TemplateResponse(req, "home.html")


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
    if not news:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"News item with ID {news_id} not found",
        )

    def convert_dt(dt):
        if dt is None:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone(timedelta(hours=-3)))

    return templates.TemplateResponse(
        req,
        "news_detail.html",
        {
            "news": {
                **news.__dict__,
                "photo_url": news.photo_url,
                "origin_created_at": convert_dt(news.origin_created_at),
                "indexed_at": convert_dt(news.indexed_at),
                "inserted_at": convert_dt(news.inserted_at),
            }
        },
    )


@app.get("/search", include_in_schema=False)
async def search(
    req: Request,
    db: Annotated[Session, Depends(get_db)],
):
    logger.info(f"query: {req.url.query}")
    return templates.TemplateResponse(req, "search.html")


@app.get("/api/news/latest", response_model=list[NewsShortResponse])
async def get_news(
    req: Request,
    db: Annotated[Session, Depends(get_db)],
    page: int = 1,
):
    logger.info("Fetching news items from the database")
    query = select(models.News).order_by(models.News.origin_created_at.desc())
    if page > 1:
        query = query.offset((page - 1) * 10)
    result = db.execute(query.limit(10))
    news_items = result.scalars().all()
    if not news_items:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No news items found",
        )
    return [
        {
            **item.__dict__,
            "photo_url": item.photo_url,
            "content": item.content[:150].replace("\n", "")[:100] + "...",
        }
        for item in news_items
    ]


@app.get("/api/news/{news_id}", response_model=NewsResponse)
async def get_news_item_api(
    news_id: int,
    req: Request,
    db: Annotated[Session, Depends(get_db)],
):
    # logger.info(f"Fetching news item with ID {news_id} from the database")
    try:
        result = db.execute(select(models.News).where(models.News.id == news_id))
        news_item = result.scalars().first()
        if not news_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"News item with ID {news_id} not found",
            )
        return news_item
    except HTTPException:
        raise
    except Exception as e:
        logger.info(f"Error fetching news item: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@app.get("/api/search", response_model=list[NewsSearchResponse])
async def api_search(
    req: Request,
    db: Annotated[Session, Depends(get_db)],
    text: str | None = None,
    origin_date_from: str | None = None,
    origin_date_to: str | None = None,
    inserted_date_from: str | None = None,
    inserted_date_to: str | None = None,
    page: int = 1,
):
    logger.info(f"API Search called with query: {req.url.query}")
    query = select(models.News)
    if text:
        query = query.where(
            models.News.title.ilike(f"%{text}%")
            | models.News.content.ilike(f"%{text}%")
        )
    if origin_date_from:
        d = datetime.fromisoformat(origin_date_from)
        query = query.where(models.News.origin_created_at >= d)
    if origin_date_to:
        d = datetime.fromisoformat(origin_date_to)
        query = query.where(models.News.origin_created_at < d + timedelta(days=1))
    if inserted_date_from:
        d = datetime.fromisoformat(inserted_date_from)
        query = query.where(models.News.inserted_at >= d)
    if inserted_date_to:
        d = datetime.fromisoformat(inserted_date_to)
        query = query.where(models.News.inserted_at < d + timedelta(days=1))
    if page > 1:
        query = query.offset((page - 1) * 50)
    result = db.execute(query.order_by(models.News.origin_created_at.desc()).limit(50))
    news_items = result.scalars().all()
    if not news_items:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No news items found matching the search criteria",
        )
    return [
        {
            **item.__dict__,
            "content": item.content[:150].replace("\n", "")[:100] + "...",
        }
        for item in news_items
    ]


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    message = exc.detail or "An error ocurred. Please check your request and try again."
    logger.info(f"pre-Rendering error page for HTTP {exc.status_code}: {message}")
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": message},
        )
    if exc.status_code == 404:
        return templates.TemplateResponse(
            request,
            "404.html",
            {
                "detail": exc.detail,
            },
            status_code=exc.status_code,
        )
    logger.info(f"Rendering error page for HTTP {exc.status_code}: {message}")
    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code": exc.status_code,
            "detail": message,
        },
        status_code=exc.status_code,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    message = "Invalid request. Please check your input and try again."
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": message, "errors": exc.errors()},
        )
    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "detail": message,
        },
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    )

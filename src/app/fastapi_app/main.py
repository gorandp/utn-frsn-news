import os
from typing import Annotated
from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

# from database_models import Base as DbBase
from .. import database_models as models
from ..logger import LogWrapper
from ..cloudflare_images import CloudflareImages
from .schemas import NewsResponse, NewsShortResponse
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
    if not news:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"News item with ID {news_id} not found",
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
        logger.info(f"Error fetching news item: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


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

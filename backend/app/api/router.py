from fastapi import APIRouter
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.chat import router as chat_router
from app.api.routes.cv_assistant import router as cv_assistant_router
from app.api.routes.documents import router as documents_router
from app.api.routes.playground import router as playground_router
from app.core.config import ALLOWED_ORIGINS, LOCALHOST_ORIGIN_REGEX

api_router = APIRouter()
api_router.include_router(chat_router)
api_router.include_router(documents_router)
api_router.include_router(cv_assistant_router)
api_router.include_router(playground_router)


def configure_cors(app) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_origin_regex=LOCALHOST_ORIGIN_REGEX,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

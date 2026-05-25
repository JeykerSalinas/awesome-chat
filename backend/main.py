from fastapi import FastAPI

from app.api.router import api_router, configure_cors
from app.db import init_db


def create_app() -> FastAPI:
    app = FastAPI(title="Lovely Chat Backend")
    configure_cors(app)
    init_db()
    app.include_router(api_router)
    return app


app = create_app()

from fastapi import FastAPI

from app.api.router import api_router, configure_cors


def create_app() -> FastAPI:
    app = FastAPI(title="Lovely Chat Backend")
    configure_cors(app)
    app.include_router(api_router)
    return app


app = create_app()

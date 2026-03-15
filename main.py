from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.routers.api import api_users, api_transactions
from app.routers import pages

app = FastAPI()

app.mount(
    "/static",
    StaticFiles(directory=Path(__file__).parent.absolute() / "static"),
    name="static",
)

app.include_router(api_users.router)
app.include_router(api_transactions.router)
app.include_router(pages.router)

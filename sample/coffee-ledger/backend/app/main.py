from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import cors_origins
from app.db import DbSessionMiddleware, init_schema
from app.errors import register_exception_handlers
from app.routers import collection, drinks, operations, payments, people, price, summary, unpaid, vault


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    init_schema()
    yield


app = FastAPI(title="coffee-ledger", lifespan=lifespan)
app.add_middleware(DbSessionMiddleware)
register_exception_handlers(app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(people.router)
app.include_router(drinks.router)
app.include_router(payments.router)
app.include_router(price.router)
app.include_router(collection.router)
app.include_router(vault.router)
app.include_router(unpaid.router)
app.include_router(summary.router)
app.include_router(operations.router)

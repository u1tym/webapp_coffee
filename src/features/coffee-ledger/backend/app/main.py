from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import cors_origins, validate_settings
from app.logging_setup import get_logger, setup_logging

validate_settings()
setup_logging()

from app.db import DbSessionMiddleware  # noqa: E402
from app.errors import register_exception_handlers  # noqa: E402
from app.routers import (  # noqa: E402
    collection,
    drinks,
    operations,
    payments,
    people,
    price,
    summary,
    unpaid,
    vault,
)

app = FastAPI(title="coffee-ledger")
app.add_middleware(DbSessionMiddleware)
register_exception_handlers(app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins(),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(people.router)
app.include_router(drinks.router)
app.include_router(payments.router)
app.include_router(unpaid.router)
app.include_router(price.router)
app.include_router(collection.router)
app.include_router(vault.router)
app.include_router(summary.router)
app.include_router(operations.router)

get_logger().info("起動 cors_origins=%s", ",".join(cors_origins()))

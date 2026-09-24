from typing import Any

from fastapi import APIRouter

from app.services import maintenance

router = APIRouter()


@router.post("/maintenance/vacuum")
def post_vacuum() -> dict[str, Any]:
    return maintenance.vacuum()

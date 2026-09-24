from typing import Any

import psycopg
from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, StrictInt, StrictStr

from app.db import get_db
from app.services import people

router = APIRouter()


class PersonCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: StrictStr


class DisplayOrderUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    person_ids: list[StrictInt]


@router.get("/people")
def get_people(
    scope: str = "active",
    conn: psycopg.Connection = Depends(get_db),
) -> dict[str, list[dict[str, Any]]]:
    return {"people": people.list_people(conn, scope)}


@router.post("/people", status_code=201)
def post_people(
    body: PersonCreate,
    conn: psycopg.Connection = Depends(get_db),
) -> dict[str, Any]:
    return people.register_person(conn, body.name)


@router.put("/people/display-order")
def put_display_order(
    body: DisplayOrderUpdate,
    conn: psycopg.Connection = Depends(get_db),
) -> dict[str, list[dict[str, Any]]]:
    return {"people": people.update_display_order(conn, list(body.person_ids))}


@router.get("/people/{person_id}")
def get_person(
    person_id: int,
    conn: psycopg.Connection = Depends(get_db),
) -> dict[str, Any]:
    return people.get_person(conn, person_id)


@router.post("/people/{person_id}/deactivate")
def post_deactivate(
    person_id: int,
    conn: psycopg.Connection = Depends(get_db),
) -> dict[str, Any]:
    return people.deactivate_person(conn, person_id)

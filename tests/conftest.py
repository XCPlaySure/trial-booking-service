import pytest

from trial_booking import repositories as repo
from trial_booking.db import connect
from trial_booking.schema import create_schema


@pytest.fixture
def conn():
    c = connect()
    create_schema(c)
    yield c
    c.close()


@pytest.fixture
def parent(conn):
    return {"id": repo.insert_parent(conn, "P", "p@x.com")}


@pytest.fixture
def student(conn, parent):
    return {"id": repo.insert_student(conn, parent["id"], "S")}


@pytest.fixture
def instructor(conn):
    return {"id": repo.insert_instructor(conn, "I", "math", "M")}


@pytest.fixture
def trial_class(conn, instructor):
    return {"id": repo.insert_class(conn, "C", instructor["id"], "2026-10-01", "10:00", 4)}

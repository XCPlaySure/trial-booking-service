import pytest

from trial_booking import repositories as repo
from trial_booking.db import connect
from trial_booking.schema import create_schema


def test_schema_ddl_executes(conn):
    tables = {r["name"] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()}
    for t in ("parent", "student", "instructor", "trial_class", "booking", "seat_reservation", "payment_attempt"):
        assert t in tables


def test_duplicate_active_rejected(conn, student, trial_class):
    repo.insert_booking(conn, student["id"], trial_class["id"], "pending_payment")
    with pytest.raises(Exception):
        repo.insert_booking(conn, student["id"], trial_class["id"], "confirmed")


def test_terminal_rebook_allowed(conn, student, trial_class):
    first = repo.insert_booking(conn, student["id"], trial_class["id"], "pending_payment")
    repo.set_booking_status(conn, first, "cancelled")
    second = repo.insert_booking(conn, student["id"], trial_class["id"], "pending_payment")
    assert second != first

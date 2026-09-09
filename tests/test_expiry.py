from datetime import datetime, timedelta, timezone

from trial_booking import repositories as repo
from trial_booking.booking_service import availability, create_booking
from trial_booking.expiry import cancel_booking, run_expiry
from trial_booking.payment import pay


def _expired_soon(conn, student, trial_class):
    bid = repo.insert_booking(conn, student["id"], trial_class["id"], "pending_payment")
    past = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
    repo.insert_reservation(conn, bid, past)
    return bid


def test_expiry_cancels_and_frees_seat(conn, student, trial_class):
    bid = _expired_soon(conn, student, trial_class)
    count = run_expiry(conn)
    assert count == 1
    assert repo.get_booking(conn, bid)["status"] == "cancelled"
    assert repo.get_reservation(conn, bid) is None
    assert availability(conn, trial_class["id"]) == 4


def test_expiry_with_string_now(conn, student, trial_class):
    bid = _expired_soon(conn, student, trial_class)
    assert run_expiry(conn, now=datetime.now(timezone.utc).isoformat()) == 1
    assert repo.get_booking(conn, bid)["status"] == "cancelled"


def test_expiry_noop_when_none(conn):
    assert run_expiry(conn) == 0


def test_cancel_pending_frees_reservation(conn, student, trial_class):
    bid = create_booking(conn, student["id"], trial_class["id"])
    cancel_booking(conn, bid)
    assert repo.get_booking(conn, bid)["status"] == "cancelled"
    assert repo.get_reservation(conn, bid) is None
    assert availability(conn, trial_class["id"]) == 4


def test_cancel_confirmed_frees_seat(conn, student, trial_class):
    bid = create_booking(conn, student["id"], trial_class["id"])
    pay(conn, bid, "test-success-1")
    cancel_booking(conn, bid)
    assert repo.get_booking(conn, bid)["status"] == "cancelled"
    assert repo.confirmed_students(conn, trial_class["id"]) == []
    assert availability(conn, trial_class["id"]) == 4


def test_cancel_terminal_raises(conn, student, trial_class):
    bid = create_booking(conn, student["id"], trial_class["id"])
    cancel_booking(conn, bid)
    try:
        cancel_booking(conn, bid)
        assert False
    except ValueError:
        pass


def test_cancel_missing_raises(conn):
    try:
        cancel_booking(conn, 999)
        assert False
    except ValueError:
        pass
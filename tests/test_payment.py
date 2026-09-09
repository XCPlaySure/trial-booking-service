import pytest

from trial_booking import repositories as repo
from trial_booking.booking_service import BookingError, availability, create_booking
from trial_booking.expiry import run_expiry
from trial_booking.payment import classify_card, pay


def _pending_booking(conn, student, trial_class):
    return create_booking(conn, student["id"], trial_class["id"])


def test_classify_card():
    assert classify_card("test-success-123") == "succeeded"
    assert classify_card("test-fail-000") == "declined"
    assert classify_card("4111111111111111") == "declined"


def test_confirm_success(conn, student, trial_class):
    bid = _pending_booking(conn, student, trial_class)
    status = pay(conn, bid, "test-success-1")
    assert status == "succeeded"
    assert repo.get_booking(conn, bid)["status"] == "confirmed"
    assert repo.get_reservation(conn, bid) is None
    roster = repo.confirmed_students(conn, trial_class["id"])
    assert len(roster) == 1


def test_decline_fails_and_releases(conn, student, trial_class):
    bid = _pending_booking(conn, student, trial_class)
    status = pay(conn, bid, "test-fail-1")
    assert status == "declined"
    assert repo.get_booking(conn, bid)["status"] == "payment_failed"
    assert repo.get_reservation(conn, bid) is None
    assert repo.confirmed_students(conn, trial_class["id"]) == []
    assert availability(conn, trial_class["id"]) == 4


def test_confirm_expired_reservation_rejected(conn, student, trial_class):
    bid = repo.insert_booking(conn, student["id"], trial_class["id"], "pending_payment")
    repo.insert_reservation(conn, bid, "2020-01-01T00:00:00+00:00")
    with pytest.raises(BookingError, match="no longer available"):
        pay(conn, bid, "test-success-1")


def test_expired_reservation_cancelled_by_job_then_pay_rejected(conn, student, trial_class):
    bid = create_booking(conn, student["id"], trial_class["id"])
    repo.delete_reservation(conn, bid)
    repo.insert_reservation(conn, bid, "2020-01-01T00:00:00+00:00")
    run_expiry(conn)
    assert repo.get_booking(conn, bid)["status"] == "cancelled"
    with pytest.raises(BookingError, match="pending_payment"):
        pay(conn, bid, "test-success-1")


def test_confirm_released_reservation_rejected(conn, student, trial_class):
    bid = _pending_booking(conn, student, trial_class)
    repo.delete_reservation(conn, bid)
    with pytest.raises(BookingError, match="no longer available"):
        pay(conn, bid, "test-success-1")


def test_confirm_class_full_rejected(conn, parent, student, trial_class):
    bid = create_booking(conn, student["id"], trial_class["id"])
    for i in range(4):
        sid = repo.insert_student(conn, parent["id"], f"o{i}")
        repo.insert_booking(conn, sid, trial_class["id"], "confirmed")
    with pytest.raises(BookingError, match="full"):
        pay(conn, bid, "test-success-1")
    assert repo.get_booking(conn, bid)["status"] == "pending_payment"


def test_pay_wrong_state(conn, student, trial_class):
    bid = repo.insert_booking(conn, student["id"], trial_class["id"], "confirmed")
    with pytest.raises(BookingError, match="pending_payment"):
        pay(conn, bid, "test-success-1")


def test_pay_missing_booking(conn):
    with pytest.raises(BookingError, match="pending_payment"):
        pay(conn, 999, "test-success-1")
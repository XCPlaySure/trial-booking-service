import pytest

from trial_booking import repositories as repo
from trial_booking.booking_service import RESERVATION_MINUTES, BookingError, availability, create_booking
from trial_booking.expiry import cancel_booking


def test_availability_full_initial(conn, student, trial_class):
    assert availability(conn, trial_class["id"]) == 4


def test_availability_subtracts_confirmed(conn, parent, trial_class):
    s1 = repo.insert_student(conn, parent["id"], "a")
    s2 = repo.insert_student(conn, parent["id"], "b")
    repo.insert_booking(conn, s1, trial_class["id"], "confirmed")
    repo.insert_booking(conn, s2, trial_class["id"], "confirmed")
    assert availability(conn, trial_class["id"]) == 2


def test_availability_subtracts_active_reservation(conn, student, trial_class):
    bid = repo.insert_booking(conn, student["id"], trial_class["id"], "pending_payment")
    repo.insert_reservation(conn, bid, "2099-01-01T00:00:00+00:00")
    assert availability(conn, trial_class["id"]) == 3


def test_create_booking_pending_and_reservation(conn, student, trial_class):
    bid = create_booking(conn, student["id"], trial_class["id"])
    booking = repo.get_booking(conn, bid)
    assert booking["status"] == "pending_payment"
    res = repo.get_reservation(conn, bid)
    from datetime import datetime
    expires = datetime.fromisoformat(res["expires_at"])
    created = datetime.fromisoformat(res["created_at"])
    delta_min = (expires - created).total_seconds() / 60
    assert delta_min == pytest.approx(RESERVATION_MINUTES)


def test_create_booking_class_full(conn, parent, trial_class):
    for i in range(4):
        sid = repo.insert_student(conn, parent["id"], f"s{i}")
        create_booking(conn, sid, trial_class["id"])
    s5 = repo.insert_student(conn, parent["id"], "s5")
    with pytest.raises(BookingError, match="full"):
        create_booking(conn, s5, trial_class["id"])


def test_duplicate_active_rejected_via_service(conn, student, trial_class):
    create_booking(conn, student["id"], trial_class["id"])
    with pytest.raises(BookingError):
        create_booking(conn, student["id"], trial_class["id"])


def test_rebook_after_terminal_allowed(conn, student, trial_class):
    bid = create_booking(conn, student["id"], trial_class["id"])
    cancel_booking(conn, bid)
    bid2 = create_booking(conn, student["id"], trial_class["id"])
    assert bid2 != bid


def test_unknown_class(conn, student):
    with pytest.raises(BookingError):
        create_booking(conn, student["id"], 999)


def test_availability_unknown_class(conn):
    with pytest.raises(BookingError):
        availability(conn, 999)


def test_unknown_student(conn, trial_class):
    with pytest.raises(BookingError):
        create_booking(conn, 999, trial_class["id"])

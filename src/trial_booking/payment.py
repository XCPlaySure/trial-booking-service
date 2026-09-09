import sqlite3
from datetime import datetime, timezone

from . import repositories as repo
from .booking_service import BookingError, confirmed_count, parse_iso


def classify_card(card_number):
    if card_number.startswith("test-success"):
        return "succeeded"
    if card_number.startswith("test-fail"):
        return "declined"
    return "declined"


def _attempt(conn, booking, card_number, status):
    repo.insert_payment_attempt(conn, booking["id"], card_number, status)
    if status == "succeeded":
        repo.set_booking_status(conn, booking["id"], "confirmed")
    else:
        repo.set_booking_status(conn, booking["id"], "payment_failed")
    repo.delete_reservation(conn, booking["id"])


def pay(conn, booking_id, card_number):
    """Apply a payment attempt and settle the booking atomically."""
    conn.execute("BEGIN IMMEDIATE")
    try:
        booking = repo.get_booking(conn, booking_id)
        if booking is None or booking["status"] != "pending_payment":
            raise BookingError("booking not in pending_payment state")

        status = classify_card(card_number)

        if status == "succeeded":
            reservation = repo.get_reservation(conn, booking_id)
            if reservation is None or parse_iso(reservation["expires_at"]) <= datetime.now(timezone.utc):
                raise BookingError("seat no longer available")
            cls = repo.get_class(conn, booking["class_id"])
            if confirmed_count(conn, booking["class_id"]) >= cls["capacity"]:
                raise BookingError("class is full")

        _attempt(conn, booking, card_number, status)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return status

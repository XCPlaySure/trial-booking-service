import sqlite3
from datetime import datetime, timedelta, timezone

from . import repositories as repo
from .db import utcnow

RESERVATION_MINUTES = 5


class BookingError(Exception):
    pass


def parse_iso(value):
    return datetime.fromisoformat(value)


def reserved_seat_count(conn, class_id):
    row = conn.execute(
        """
        SELECT COUNT(*)
        FROM seat_reservation sr
        JOIN booking b ON b.id = sr.booking_id
        WHERE b.class_id = ? AND sr.expires_at > ?
        """,
        (class_id, utcnow()),
    ).fetchone()
    return row[0]


def confirmed_count(conn, class_id):
    row = conn.execute(
        "SELECT COUNT(*) FROM booking WHERE class_id=? AND status='confirmed'",
        (class_id,),
    ).fetchone()
    return row[0]


def availability(conn, class_id):
    cls = repo.get_class(conn, class_id)
    if cls is None:
        raise BookingError("class not found")
    used = confirmed_count(conn, class_id) + reserved_seat_count(conn, class_id)
    return max(0, cls["capacity"] - used)


def create_booking(conn, student_id, class_id):
    if repo.get_student(conn, student_id) is None:
        raise BookingError("student not found")
    if repo.get_class(conn, class_id) is None:
        raise BookingError("class not found")

    conn.execute("BEGIN IMMEDIATE")
    try:
        if availability(conn, class_id) <= 0:
            raise BookingError("class is full")
        try:
            booking_id = repo.insert_booking(conn, student_id, class_id, "pending_payment")
        except sqlite3.IntegrityError:
            raise BookingError("student already has an active booking for this class")
        expires_at = (datetime.now(timezone.utc) + timedelta(minutes=RESERVATION_MINUTES)).isoformat()
        repo.insert_reservation(conn, booking_id, expires_at)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return booking_id

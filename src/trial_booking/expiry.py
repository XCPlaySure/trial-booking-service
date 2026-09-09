from datetime import datetime, timezone

from . import repositories as repo


def run_expiry(conn, now=None):
    now = now or datetime.now(timezone.utc)
    if isinstance(now, str):
        now = datetime.fromisoformat(now)
    rows = conn.execute(
        "SELECT * FROM seat_reservation WHERE expires_at < ?",
        (now.isoformat(),),
    ).fetchall()
    count = 0
    for row in rows:
        booking = repo.get_booking(conn, row["booking_id"])
        if booking and booking["status"] == "pending_payment":
            repo.set_booking_status(conn, booking["id"], "cancelled")
        repo.delete_reservation(conn, row["booking_id"])
        count += 1
    return count


def cancel_booking(conn, booking_id):
    booking = repo.get_booking(conn, booking_id)
    if booking is None:
        raise ValueError("booking not found")
    if booking["status"] not in ("pending_payment", "confirmed"):
        raise ValueError("booking is already terminal")
    repo.set_booking_status(conn, booking_id, "cancelled")
    repo.delete_reservation(conn, booking_id)

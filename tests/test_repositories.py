from trial_booking import repositories as repo


def test_round_trip_parent(conn):
    pid = repo.insert_parent(conn, "Alice", "a@x.com")
    row = conn.execute("SELECT * FROM parent WHERE id=?", (pid,)).fetchone()
    assert row["name"] == "Alice"
    assert row["email"] == "a@x.com"
    assert row["created_at"] and row["updated_at"]


def test_round_trip_student(conn, parent):
    sid = repo.insert_student(conn, parent["id"], "Sam")
    row = conn.execute("SELECT * FROM student WHERE id=?", (sid,)).fetchone()
    assert row["name"] == "Sam" and row["parent_id"] == parent["id"]


def test_round_trip_instructor_class(conn, instructor):
    cid = repo.insert_class(conn, "Math", instructor["id"], "2026-10-01", "10:00")
    row = conn.execute("SELECT * FROM trial_class WHERE id=?", (cid,)).fetchone()
    assert row["capacity"] == 4


def test_booking_update_status(conn, student, trial_class):
    bid = repo.insert_booking(conn, student["id"], trial_class["id"], "pending_payment")
    repo.set_booking_status(conn, bid, "confirmed")
    assert repo.get_booking(conn, bid)["status"] == "confirmed"


def test_reservation_crud(conn, student, trial_class, monkeypatch):
    from trial_booking.db import utcnow
    bid = repo.insert_booking(conn, student["id"], trial_class["id"], "pending_payment")
    rid = repo.insert_reservation(conn, bid, "2099-01-01T00:00:00+00:00")
    assert repo.get_reservation(conn, bid)["id"] == rid
    repo.delete_reservation(conn, bid)
    assert repo.get_reservation(conn, bid) is None


def test_confirmed_students_roster(conn, student, trial_class):
    repo.insert_booking(conn, student["id"], trial_class["id"], "confirmed")
    roster = repo.confirmed_students(conn, trial_class["id"])
    assert len(roster) == 1 and roster[0]["student_name"] == "S"

import sqlite3

from .db import utcnow


def _insert(conn, table, data):
    now = utcnow()
    cols = {**data, "created_at": now, "updated_at": now}
    keys = ",".join(cols)
    placeholders = ",".join("?" for _ in cols)
    cur = conn.execute(
        f"INSERT INTO {table} ({keys}) VALUES ({placeholders})",
        list(cols.values()),
    )
    return cur.lastrowid


def _update(conn, table, row_id, data):
    cols = {**data, "updated_at": utcnow()}
    assignments = ",".join(f"{k}=?" for k in cols)
    conn.execute(
        f"UPDATE {table} SET {assignments} WHERE id=?",
        list(cols.values()) + [row_id],
    )


def insert_parent(conn, name, email):
    return _insert(conn, "parent", {"name": name, "email": email})


def insert_student(conn, parent_id, name):
    return _insert(conn, "student", {"parent_id": parent_id, "name": name})


def insert_instructor(conn, name, subject, gender):
    return _insert(conn, "instructor", {"name": name, "subject": subject, "gender": gender})


def insert_class(conn, name, instructor_id, date, time, capacity=4):
    return _insert(
        conn,
        "trial_class",
        {"name": name, "instructor_id": instructor_id, "date": date, "time": time, "capacity": capacity},
    )


def insert_booking(conn, student_id, class_id, status):
    return _insert(conn, "booking", {"student_id": student_id, "class_id": class_id, "status": status})


def insert_reservation(conn, booking_id, expires_at):
    return _insert(conn, "seat_reservation", {"booking_id": booking_id, "expires_at": expires_at})


def insert_payment_attempt(conn, booking_id, card_number, status):
    return _insert(
        conn,
        "payment_attempt",
        {"booking_id": booking_id, "card_number": card_number, "status": status},
    )


def get_booking(conn, booking_id):
    row = conn.execute("SELECT * FROM booking WHERE id=?", (booking_id,)).fetchone()
    return dict(row) if row else None


def get_student(conn, student_id):
    row = conn.execute("SELECT * FROM student WHERE id=?", (student_id,)).fetchone()
    return dict(row) if row else None


def get_class(conn, class_id):
    row = conn.execute("SELECT * FROM trial_class WHERE id=?", (class_id,)).fetchone()
    return dict(row) if row else None


def set_booking_status(conn, booking_id, status):
    _update(conn, "booking", booking_id, {"status": status})


def get_reservation(conn, booking_id):
    row = conn.execute(
        "SELECT * FROM seat_reservation WHERE booking_id=?", (booking_id,)
    ).fetchone()
    return dict(row) if row else None


def delete_reservation(conn, booking_id):
    conn.execute("DELETE FROM seat_reservation WHERE booking_id=?", (booking_id,))


def list_classes(conn):
    return [dict(r) for r in conn.execute("SELECT * FROM trial_class ORDER BY id").fetchall()]


def confirmed_students(conn, class_id):
    rows = conn.execute(
        """
        SELECT s.id AS student_id, s.name AS student_name
        FROM booking b
        JOIN student s ON s.id = b.student_id
        WHERE b.class_id = ? AND b.status = 'confirmed'
        """,
        (class_id,),
    ).fetchall()
    return [dict(r) for r in rows]

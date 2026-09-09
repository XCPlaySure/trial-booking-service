SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS parent (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS student (
    id INTEGER PRIMARY KEY,
    parent_id INTEGER NOT NULL REFERENCES parent(id),
    name TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS instructor (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    subject TEXT NOT NULL,
    gender TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS trial_class (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    instructor_id INTEGER NOT NULL REFERENCES instructor(id),
    date TEXT NOT NULL,
    time TEXT NOT NULL,
    capacity INTEGER NOT NULL DEFAULT 4,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS booking (
    id INTEGER PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES student(id),
    class_id INTEGER NOT NULL REFERENCES trial_class(id),
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS seat_reservation (
    id INTEGER PRIMARY KEY,
    booking_id INTEGER NOT NULL UNIQUE REFERENCES booking(id),
    expires_at TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS payment_attempt (
    id INTEGER PRIMARY KEY,
    booking_id INTEGER NOT NULL REFERENCES booking(id),
    card_number TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_active_booking
    ON booking(student_id, class_id)
    WHERE status IN ('pending_payment', 'confirmed');
"""


def create_schema(conn):
    conn.executescript(SCHEMA_SQL)

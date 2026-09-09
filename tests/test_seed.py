from trial_booking.booking_service import availability, confirmed_count
from trial_booking.seed import seed


def test_seed_counts(conn):
    _, students, instructors, classes = seed(conn)
    assert len(students) == 5
    assert len(instructors) == 2
    assert len(classes) == 3
    assert [r[0] for r in conn.execute("SELECT COUNT(*) FROM parent")] == [2]
from trial_booking.booking_service import availability, confirmed_count
from trial_booking.seed import seed


def test_seed_counts(conn):
    _, students, instructors, classes = seed(conn)
    assert len(students) == 4
    assert len(instructors) == 2
    assert len(classes) == 3
    assert [r[0] for r in conn.execute("SELECT COUNT(*) FROM parent")] == [2]


def test_seed_c1_available(conn):
    seed(conn)
    c1 = conn.execute("SELECT id FROM trial_class WHERE name='Math 101'").fetchone()["id"]
    assert availability(conn, c1) == 4


def test_seed_c2_near_capacity(conn):
    seed(conn)
    c2 = conn.execute("SELECT id FROM trial_class WHERE name='Science 101'").fetchone()["id"]
    assert confirmed_count(conn, c2) == 3
    assert availability(conn, c2) == 1


def test_seed_c3_full(conn):
    seed(conn)
    c3 = conn.execute("SELECT id FROM trial_class WHERE name='Cram School'").fetchone()["id"]
    assert confirmed_count(conn, c3) == 4
    assert availability(conn, c3) == 0

def test_seed_c1_available(conn):
    seed(conn)
    c1 = conn.execute("SELECT id FROM trial_class WHERE name='Math 101'").fetchone()["id"]
    assert availability(conn, c1) == 4


def test_seed_c2_near_capacity(conn):
    seed(conn)
    c2 = conn.execute("SELECT id FROM trial_class WHERE name='Science 101'").fetchone()["id"]
    assert confirmed_count(conn, c2) == 3
    assert availability(conn, c2) == 1


def test_seed_c3_full(conn):
    seed(conn)
    c3 = conn.execute("SELECT id FROM trial_class WHERE name='Cram School'").fetchone()["id"]
    assert confirmed_count(conn, c3) == 4
    assert availability(conn, c3) == 0
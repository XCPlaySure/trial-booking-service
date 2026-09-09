import os
import tempfile
import threading

from trial_booking import repositories as repo
from trial_booking.booking_service import BookingError, availability, create_booking
from trial_booking.db import connect
from trial_booking.payment import pay
from trial_booking.schema import create_schema


def _setup(path):
    conn = connect(path)
    conn.execute("PRAGMA busy_timeout=5000")
    create_schema(conn)
    pid = repo.insert_parent(conn, "P", "p@x.com")
    iid = repo.insert_instructor(conn, "I", "s", "M")
    cid = repo.insert_class(conn, "C", iid, "2026-01-01", "10:00", 4)
    students = [repo.insert_student(conn, pid, f"s{i}") for i in range(4)]
    for i in range(3):
        repo.insert_booking(conn, students[i], cid, "confirmed")
    conn.commit()
    conn.close()
    return students[3], cid


def test_last_seat_race_exactly_one_confirmed():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "race.db")
        contender, cid = _setup(path)

        results = []
        barrier = threading.Barrier(2)

        def compete():
            c = connect(path)
            c.execute("PRAGMA busy_timeout=5000")
            try:
                barrier.wait()
                try:
                    bid = create_booking(c, contender, cid)
                    results.append(("won", bid))
                except BookingError:
                    results.append(("lost", None))
            finally:
                c.close()

        t1 = threading.Thread(target=compete)
        t2 = threading.Thread(target=compete)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        winners = [r for r in results if r[0] == "won"]
        assert len(winners) == 1
        assert len([r for r in results if r[0] == "lost"]) == 1

        bid = winners[0][1]
        winner_conn = connect(path)
        winner_conn.execute("PRAGMA busy_timeout=5000")
        assert pay(winner_conn, bid, "test-success-1") == "succeeded"
        winner_conn.close()
        check = connect(path)
        n = check.execute("SELECT COUNT(*) FROM booking WHERE class_id=? AND status='confirmed'", (cid,)).fetchone()[0]
        assert n == 4
        assert availability(check, cid) == 0
        check.close()


def test_last_seat_race_one_winner_confirms_other_cannot():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "race.db")
        contender, cid = _setup(path)
        c1 = connect(path)
        c1.execute("PRAGMA busy_timeout=5000")
        c2 = connect(path)
        c2.execute("PRAGMA busy_timeout=5000")

        bid = create_booking(c1, contender, cid)
        try:
            create_booking(c2, contender, cid)
            assert False, "second create on same student/seat must fail"
        except BookingError:
            pass
        assert pay(c1, bid, "test-success-1") == "succeeded"
        assert availability(c1, cid) == 0
        c1.close()
        c2.close()
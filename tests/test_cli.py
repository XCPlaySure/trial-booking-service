from trial_booking import repositories as repo
from trial_booking.cli import main
from trial_booking.db import connect


def _run(tmp_path, args):
    db = str(tmp_path / "test.db")
    code = main(["--db", db] + args)
    assert code == 0
    return db


def _conn(db):
    return connect(db)


def test_cli_seed_and_list(tmp_path):
    db = _run(tmp_path, ["seed"])
    with _conn(db) as c:
        assert [r[0] for r in c.execute("SELECT COUNT(*) FROM trial_class")] == [3]
    _run(tmp_path, ["list"])


def test_cli_booking_flow(tmp_path):
    db = _run(tmp_path, ["seed"])
    with _conn(db) as c:
        s1 = c.execute("SELECT id FROM student ORDER BY id LIMIT 1").fetchone()["id"]
        c1 = c.execute("SELECT id FROM trial_class WHERE name='Math 101'").fetchone()["id"]
        s4 = c.execute("SELECT id FROM student ORDER BY id LIMIT 1 OFFSET 3").fetchone()["id"]
        c2 = c.execute("SELECT id FROM trial_class WHERE name='Science 101'").fetchone()["id"]
    _run(tmp_path, ["create-booking", "--student-id", str(s1), "--class-id", str(c1)])
    _run(tmp_path, ["create-booking", "--student-id", str(s4), "--class-id", str(c2)])
    with _conn(db) as c:
        bid = c.execute(
            "SELECT id FROM booking WHERE student_id=? AND status='pending_payment' LIMIT 1", (s1,)
        ).fetchone()["id"]
        bid2 = c.execute(
            "SELECT id FROM booking WHERE student_id=? AND status='pending_payment' LIMIT 1", (s4,)
        ).fetchone()["id"]
    _run(tmp_path, ["confirm", "--booking-id", str(bid), "--card", "test-success-1"])
    _run(tmp_path, ["confirm", "--booking-id", str(bid2), "--card", "test-fail-1"])
    _run(tmp_path, ["roster", "--class-id", str(c1)])
    _run(tmp_path, ["cancel", "--booking-id", str(bid)])
    _run(tmp_path, ["expiry"])


def test_cli_demo(tmp_path):
    db = _run(tmp_path, ["demo"])
    with _conn(db) as c:
        n_confirmed = c.execute("SELECT COUNT(*) FROM booking WHERE status='confirmed'").fetchone()[0]
        assert n_confirmed == 9  # C1:1 + C2:4 + C3:4
        n_failed = c.execute("SELECT COUNT(*) FROM booking WHERE status='payment_failed'").fetchone()[0]
        assert n_failed == 1
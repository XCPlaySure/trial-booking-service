import argparse
import os

from . import repositories as repo
from .booking_service import availability, create_booking
from .db import connect
from .expiry import cancel_booking, run_expiry
from .payment import pay
from .schema import create_schema
from .seed import seed

DEFAULT_DB = "trial_booking.db"


def _conn(args):
    return connect(args.db)


def cmd_list(conn, args):
    for cls in repo.list_classes(conn):
        avail = availability(conn, cls["id"])
        print(f"{cls['id']}: {cls['name']} ({cls['date']} {cls['time']}) capacity={cls['capacity']} available={avail}")


def cmd_seed(conn, args):
    _, students, _, classes = seed(conn)
    print("seeded")
    for cid in classes:
        print(f"class {cid} confirmed={repo.confirmed_students(conn, cid)}")


def cmd_create(conn, args):
    bid = create_booking(conn, args.student_id, args.class_id)
    print(f"booking {bid} status=pending_payment")


def cmd_confirm(conn, args):
    status = pay(conn, args.booking_id, args.card)
    print(f"booking {args.booking_id} status={status}")


def cmd_cancel(conn, args):
    cancel_booking(conn, args.booking_id)
    print(f"booking {args.booking_id} cancelled")


def cmd_roster(conn, args):
    for s in repo.confirmed_students(conn, args.class_id):
        print(s["student_name"])


def cmd_expiry(conn, args):
    count = run_expiry(conn)
    print(f"expired {count} reservations")


def cmd_demo(conn, args):
    seed(conn)
    students = [r["id"] for r in conn.execute("SELECT id FROM student ORDER BY id").fetchall()]
    classes = [r["id"] for r in conn.execute("SELECT id FROM trial_class ORDER BY id").fetchall()]
    s1, s2, s3, s4 = students
    c1, c2, c3 = classes

    print("-- demo: available booking (S1 on C1)")
    b1 = create_booking(conn, s1, c1)
    print(f"booking {b1} -> {pay(conn, b1, 'test-success-1111')}")

    print("-- demo: near-capacity race (S4 on C2 fills it)")
    b2 = create_booking(conn, s4, c2)
    print(f"booking {b2} -> {pay(conn, b2, 'test-success-2222')}")

    print("-- demo: duplicate rebook (S1 on C2) rejected")
    try:
        create_booking(conn, s1, c2)
        print("UNEXPECTED: accepted")  # pragma: no cover
    except Exception as e:
        print(f"rejected: {e}")

    print("-- demo: payment failure (S2 on C1, bad card)")
    b3 = create_booking(conn, s2, c1)
    print(f"booking {b3} -> {pay(conn, b3, 'test-fail-0000')}")
    print(f"availability C1 after failure: {availability(conn, c1)}")


def main(argv=None):
    parser = argparse.ArgumentParser(prog="trial_booking")
    parser.add_argument("--db", default=DEFAULT_DB, help="SQLite database file")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list")
    sub.add_parser("seed")
    p = sub.add_parser("create-booking")
    p.add_argument("--student-id", type=int, required=True)
    p.add_argument("--class-id", type=int, required=True)
    p = sub.add_parser("confirm")
    p.add_argument("--booking-id", type=int, required=True)
    p.add_argument("--card", required=True)
    p = sub.add_parser("cancel")
    p.add_argument("--booking-id", type=int, required=True)
    p = sub.add_parser("roster")
    p.add_argument("--class-id", type=int, required=True)
    sub.add_parser("expiry")
    sub.add_parser("demo")

    args = parser.parse_args(argv)

    if os.path.exists(args.db):
        conn = _conn(args)
    else:
        conn = _conn(args)
        create_schema(conn)

    handlers = {
        "list": cmd_list,
        "seed": cmd_seed,
        "create-booking": cmd_create,
        "confirm": cmd_confirm,
        "cancel": cmd_cancel,
        "roster": cmd_roster,
        "expiry": cmd_expiry,
        "demo": cmd_demo,
    }
    try:
        handlers[args.command](conn, args)
    finally:
        conn.close()
    return 0

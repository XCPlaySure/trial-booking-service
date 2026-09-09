# Trial Booking Service

A Python 3 + SQLite trial-class booking system. Parents pick a child and an
available trial class, submit a booking, run a deterministic mock payment, and
see the result. Teachers/admins can view confirmed class rosters.

The core challenge is integrity under concurrency: at most one confirmed
booking per child and class, a hard capacity of 4 confirmed students per
class, and at most one confirmed booking for the last available seat when two
users compete for it.

## What it does

- **Booking lifecycle**: `pending_payment -> confirmed | payment_failed | cancelled`, `confirmed -> cancelled`.
- **Seat reservation**: creating a booking atomically creates a `seat_reservation` that expires 5 minutes later.
- **Mock payment**: deterministic by card number. `test-success-*` succeeds, `test-fail-*` declines, anything else declines.
- **Roster**: confirmed students per class, excluding all other states.
- **Seed data**: 2 parents, 4 students, 2 instructors, 3 classes demonstrating availability, near-capacity, a duplicate attempt, and a payment failure.
- **CLI**: no server process, pure command surface over a unit-testable service layer.

## Requirements

- Python 3.10+
- SQLite (stdlib `sqlite3`, no runtime dependencies)

## Setup

```bash
pip install -e ".[dev]"
```

Use a virtualenv if your system Python is externally managed (PEP 668).

## Run

```bash
# seed a fresh database
python -m trial_booking --db trial_booking.db seed

# list classes with availability
python -m trial_booking --db trial_booking.db list

# create a booking (student picks a class)
python -m trial_booking --db trial_booking.db create-booking --student-id 1 --class-id 1

# confirm with a mock card
python -m trial_booking --db trial_booking.db confirm --booking-id 8 --card test-success-1111

# cancel a booking
python -m trial_booking --db trial_booking.db cancel --booking-id 8

# show a class roster
python -m trial_booking --db trial_booking.db roster --class-id 2

# run the reservation-expiry job
python -m trial_booking --db trial_booking.db expiry

# run the full demo scenario end-to-end
python -m trial_booking --db trial_booking.db demo
```

`Makefile` shortcuts: `make install`, `make test`, `make coverage`, `make seed`.

## Tests & coverage

```bash
pytest -v
coverage run -m pytest && coverage report   # targets 100% on src/trial_booking
```

Coverage config lives in `pyproject.toml` (`fail_under = 100`).

## Statuses and seat semantics

| Status        | Seat          | Roster |
|---------------|---------------|--------|
| `pending_payment` | reserved (locked) | no |
| `confirmed`   | taken         | yes    |
| `payment_failed` | free        | no     |
| `cancelled`   | free          | no     |

`payment_failed` and `cancelled` are terminal. A terminal booking does not
block a future rebooking of the same child and class.

## Architecture decisions

- **`src/` layout** with the package under `src/trial_booking/`, stdlib-only at runtime.
- **Schemas** live in `schema.py`; single `create_schema(conn)` executes DDL and creates the partial unique index.
- **Repositories** (`repositories.py`) are thin row-mapping helpers for each entity with `created_at`/`updated_at` everywhere.
- **Services** (`booking_service.py`, `payment.py`, `expiry.py`) are pure functions from `(db, params)` to `(outcome)`, directly unit-testable.
- **CLI** (`cli.py`, dispatched from `python -m trial_booking`) is a thin layer over the services. No web/API layer and no server process by design.

## Race-condition approach and tradeoffs

**Reservation table**

1. Availability = `capacity - confirmed - active_reservations`.
2. Booking creation opens a `BEGIN IMMEDIATE` write transaction, re-checks
   availability, inserts a `pending_payment` booking and a 5-minute
   `seat_reservation` atomically. Duplicate active bookings are rejected by a
   partial unique index on `(student_id, class_id)` filtered to active statuses.
3. Confirm re-opens `BEGIN IMMEDIATE`, re-checks that the reservation is still
   active and unexpired *and* that the confirmed count is still under capacity,
   then sets `confirmed` and deletes the reservation. Any check failing rolls
   the whole confirm back.

Because SQLite serializes write transactions, two users competing for the last
seat cannot both obtain an active reservation. The loser's create (or confirm)
fails on re-check and rolls back. The last-seat race therefore yields at most
one `confirmed` booking.

**Tradeoffs accepted**

- A seat is locked while a pending payment is active, so availability
  under-represents until release. Chosen for integrity over utilization.
- Reservation expiry requires a background job (`expiry` command) to release
  stale holds and cancel their bookings.
- Mock gateway is deterministic (no retries, one payment attempt per booking);
  this keeps the payment decision simple and terminal.

## Deliberate cuts

- Real payment gateway, refunds, and payment retries.
- Provider-initiated cancellation and self-service cancellation of the expiry timer.
- A web/API layer or identity/auth.
- Periodic scheduling of the expiry job in-process (the `expiry` command is a runnable unit).

## Release monitoring

- `pending_payment` dwell time and expiry-job success/failure rates.
- Rejection counts (class full, duplicate active booking) as booking-conversion signal.
- Confirmed-vs-availability ratios per class to tune capacity.

## Next steps

- Add a real payment provider behind the `classify_card` seam.
- Run the expiry job on a schedule (cron/systemd) or move to a queue.
- Add a web/API layer and identity.
- Swap SQLite for a row-locking DB if concurrent write throughput becomes a bottleneck.
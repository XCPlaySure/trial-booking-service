# AI_USAGE.md


## AI tools used
- Antigravity-CLI
- Github Copilot

## What I used AI for
I let the AI to build the code, I do detail specification of the project like
- Scaffolding the package layout
- Enforcing best practices
- Drafting the SQLite schema
- Defining rules for the project flow, scenario, and test coverage

## One place AI helped me move faster
- AI help me build the code and that is really save a low of my time

## One place I disagreed with, corrected, or rejected AI output
Let say this is the race condition scenario:

```
Timeline:
  T1: User A sees class (3 confirmed, 1 available)
  T2: User A starts booking (pending_payment)
  T3: User B sees class (3 confirmed, 1 available) 
  T4: User B starts booking (pending_payment)
  T5: User B pays, confirms → 4 confirmed
  T6: User A pays → should fail, but how?
```

The race condition flow is core technical challenge. The Ai consult and showing option the tackle this:
1. Count pending_payment in capacity
    ```
    Availability = capacity - (confirmed + pending_payment)
    T1: User A sees: 4 - (3 + 0) = 1 available ✓
    T2: User A books: pending_payment created
    T3: User B sees: 4 - (3 + 1) = 0 available ✗ (blocked)
    ```
2. Optimistic locking on confirm
    ```
    T1-T4: Both users book freely
    T5: User B confirms → version check passes
    T6: User A confirms → version check fails (version mismatch)
    ```
3. Reservation table
    ```
    Separate table: seat_reservation (class_id, user_id, expires_at)
    Lock seat on selection, release on timeout/failure
    ```
I choose option 3 because it handled more clear in the data status rather some on the fly checking condition.

## What I'd change about my AI workflow next time
- Specifically push for a two-different-children race test
  instead of accepting a same-student test as sufficient coverage of the
  last-seat scenario.

## How I verified the final implementation
- `pytest -v` (49/49 passing)
- `coverage report` (100% on
  src/trial_booking)
- the `demo` CLI command run end-to-end
- manually running two real `create-booking` processes concurrently against the
  same seeded database to confirm the last-seat race resolves cleanly.
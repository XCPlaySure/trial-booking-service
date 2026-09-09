from . import repositories as repo

SEED_PLAN = {
    "parents": [
        ("Alice Parent", "alice@example.com"),
        ("Bob Parent", "bob@example.com"),
    ],
    "students": [
        ("Sam", 1),
        ("Sara", 1),
        ("Tom", 2),
        ("Tina", 2),
    ],
    "instructors": [
        ("Ms. Green", "math", "F"),
        ("Mr. Blue", "science", "M"),
    ],
    "classes": [
        ("Math 101", 1, "2026-10-01", "10:00", 4),
        ("Science 101", 2, "2026-10-02", "11:00", 4),
        ("Cram School", 1, "2026-10-03", "14:00", 4),
    ],
    # class_id (by index) -> list of student_id (by index) with confirmed bookings
    "confirmed_per_class": {
        0: [],                 # C1 available
        1: [0, 1, 2],         # C2 3 confirmed -> 1 seat left
        2: [0, 1, 2, 3],      # C3 full (4)
    },
}


def seed(conn):
    parent_ids = [repo.insert_parent(conn, name, email) for name, email in SEED_PLAN["parents"]]
    student_ids = [repo.insert_student(conn, pid, name) for name, pid in SEED_PLAN["students"]]
    instructor_ids = [repo.insert_instructor(conn, name, subject, gender) for name, subject, gender in SEED_PLAN["instructors"]]
    class_ids = [repo.insert_class(conn, name, iid, date, time, cap) for name, iid, date, time, cap in SEED_PLAN["classes"]]

    for class_idx, student_idxs in SEED_PLAN["confirmed_per_class"].items():
        for student_idx in student_idxs:
            repo.insert_booking(conn, student_ids[student_idx], class_ids[class_idx], "confirmed")

    conn.commit()
    return parent_ids, student_ids, instructor_ids, class_ids

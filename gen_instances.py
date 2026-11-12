"""
Random instance generator and brute-force reference solver.

Used by the tests (every Z3 model is checked against exhaustive search on tiny
instances) and by benchmark.py (scaling and phase-transition study).
"""
import random
from itertools import product

from cw1_solver import NO_EXTRAS, Instance, check_timetable


def random_instance(n_students, n_exams, n_slots, n_rooms, exams_per_student=(1, 3),
                    capacity=(1, 10), seed=None):
    """Each student takes a random number of different exams in exams_per_student;
    room capacities are random in capacity.

    exams_per_student and capacity are (low, high) ranges, both ends included.
    The same seed always gives the same instance, so tests and benchmark runs
    can be repeated exactly.
    """
    rng = random.Random(seed)
    inst = Instance()
    inst.number_of_students, inst.number_of_exams = n_students, n_exams
    inst.number_of_slots, inst.number_of_rooms = n_slots, n_rooms
    inst.room_capacities = [rng.randint(*capacity) for _ in range(n_rooms)]
    for s in range(n_students):
        k = min(n_exams, rng.randint(*exams_per_student))
        inst.exams_to_students += [(e, s) for e in sorted(rng.sample(range(n_exams), k))]
    return inst


def write_instance(inst, path):
    """Write inst in the instance text format (the same format read_file reads).

    Handy for saving a random instance to try on the command line.
    """
    lines = [f"Number of students: {inst.number_of_students}",
             f"Number of exams: {inst.number_of_exams}",
             f"Number of slots: {inst.number_of_slots}",
             f"Number of rooms: {inst.number_of_rooms}"]
    lines += [f"Room {r} capacity: {c}" for r, c in enumerate(inst.room_capacities)]
    lines += [f"{e} {s}" for e, s in inst.exams_to_students]
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")


def brute_force(inst, extras=NO_EXTRAS):
    """Every valid timetable, by trying all (|T|*|R|)^|E| assignments and keeping
    those the plain-Python checker accepts. Only for tiny instances.

    This is the "ground truth" the tests compare every Z3 model against: if a
    model says unsat but brute force finds a timetable (or the other way
    round), the model has a bug. cells is every (slot, room) place an exam can go.
    """
    cells = list(product(range(inst.number_of_slots), range(inst.number_of_rooms)))
    return [dict(enumerate(choice)) for choice in product(cells, repeat=inst.number_of_exams)
            if not check_timetable(inst, dict(enumerate(choice)), extras)]

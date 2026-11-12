"""Tests for cw1_solver.py. Run: pytest -q tests

What is tested (103 tests in total):
  - the 20 supplied instances give their labelled answer under every model,
    and every timetable passes the plain-Python checker;
  - the checker itself spots each broken rule (C1-C5, X1-X5);
  - every model agrees with brute-force search on 550 random tiny instances,
    with and without random extra constraints;
  - --count, --explain and --optimize give the same answers as brute force;
  - the file reader, edge cases (0 exams / slots / rooms) and the command line.
"""
import glob
import os
import random
from itertools import product

import pytest
import z3

from cw1_solver import (
    MODELS,
    NO_EXTRAS,
    Extras,
    Instance,
    at_most,
    build_bool,
    check_timetable,
    count_timetables,
    explain_unsat,
    get_student_data,
    main,
    optimise,
    read_file,
    solve,
)
from gen_instances import brute_force, random_instance, write_instance

# HERE is the Solver_Code folder (one level above tests/).
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INSTANCES = sorted(glob.glob(os.path.join(HERE, "inst", "*.txt")))


def load(name):
    """Read one supplied instance by file name, e.g. load("sat1.txt")."""
    return read_file(os.path.join(HERE, "inst", name))


def expected(path):
    """The label in the file name: unsatN.txt -> "unsat", satN.txt -> "sat"."""
    return "unsat" if os.path.basename(path).startswith("unsat") else "sat"


def make_instance(slots, capacities, enrolments, n_students, n_exams):
    """Build a small hand-made Instance directly, without a file."""
    inst = Instance()
    inst.number_of_students, inst.number_of_exams = n_students, n_exams
    inst.number_of_slots, inst.number_of_rooms = slots, len(capacities)
    inst.room_capacities, inst.exams_to_students = list(capacities), list(enrolments)
    return inst


def random_extras(rng, inst):
    """A random mix of X1-X5 with small parameters."""
    def pick():
        return rng.random() < 0.4
    rooms, slots = max(inst.number_of_rooms, 1), max(inst.number_of_slots, 1)
    return Extras(
        max_per_day=(rng.randint(1, 2), rng.randint(1, 3)) if pick() else None,
        unavailable=frozenset((rng.randrange(rooms), rng.randrange(slots))
                              for _ in range(rng.randint(1, 2))) if pick() else frozenset(),
        invigilators=(rng.randint(1, 3), rng.randint(1, 3)) if pick() else None,
        min_gap=rng.randint(2, 3) if pick() else None,
        large_early=(rng.randint(1, 3), rng.randint(0, 2)) if pick() else None)


def tiny_instance(rng):
    """A random instance small enough for brute_force (at most 4 exams, 4 slots,
    2 rooms). Zero exams, slots or rooms are allowed, to test edge cases."""
    return random_instance(n_students=rng.randint(1, 6), n_exams=rng.randint(0, 4),
                           n_slots=rng.randint(0, 4), n_rooms=rng.randint(0, 2),
                           exams_per_student=(1, 3), capacity=(0, 4), seed=rng.randrange(10**9))


def as_sorted(timetable):
    """A timetable as a sorted tuple, so lists of timetables can be compared."""
    return tuple(sorted(timetable.items()))


# ---- the 20 supplied instances ----------------------------------------------

def test_all_supplied_instances_present():
    assert len(INSTANCES) == 20


@pytest.mark.parametrize("model", MODELS)
@pytest.mark.parametrize("path", INSTANCES, ids=os.path.basename)
def test_supplied_instance(path, model):
    """20 files x 3 models = 60 tests: the answer matches the label, and the
    timetable (if any) passes the independent checker."""
    inst = read_file(path)
    res = solve(inst, model)
    assert res.status == expected(path)
    if res.timetable is not None:
        assert check_timetable(inst, res.timetable) == []


@pytest.mark.parametrize("name", ["unsat5.txt", "unsat6.txt", "unsat8.txt", "unsat10.txt"])
def test_c5_is_needed_for_these_unsat_labels(name):
    """These are sat under C1-C4 alone, so their 'unsat' label needs C5."""
    groups, _, _ = build_bool(load(name), NO_EXTRAS)
    s = z3.Solver()
    for g, constraints in groups.items():
        if g != "C5":
            s.add(constraints)
    assert s.check() == z3.sat


# ---- the plain-Python checker -------------------------------------------------

def test_checker_flags_each_main_constraint():
    """Break each main rule on purpose and check the checker reports it."""
    inst = load("sat2.txt")  # exam 0 {s0, s1}, exam 1 {s0}; 3 slots, 1 room of capacity 2
    assert check_timetable(inst, {0: (0, 0), 1: (2, 0)}) == []
    assert any(v.startswith("C1") for v in check_timetable(inst, {0: (0, 0)}))
    assert any(v.startswith("C1") for v in check_timetable(inst, {0: (0, 0), 1: (5, 0)}))
    assert any(v.startswith("C2") for v in check_timetable(inst, {0: (0, 0), 1: (0, 0)}))
    assert any(v.startswith("C4") for v in check_timetable(inst, {0: (0, 0), 1: (1, 0)}))
    small = load("unsat2.txt")  # exam 0 has 2 students, room capacity 1
    assert any(v.startswith("C3") for v in check_timetable(small, {0: (0, 0), 1: (1, 0)}))


def test_checker_flags_same_slot_clash():
    inst = make_instance(1, [5, 5], [(0, 0), (1, 0)], n_students=1, n_exams=2)
    assert any(v.startswith("C5") for v in check_timetable(inst, {0: (0, 0), 1: (0, 1)}))


def test_checker_flags_extra_constraints():
    """A timetable valid for C1-C5 that each extra rule (set tightly) rejects."""
    inst, tt = load("sat2.txt"), {0: (0, 0), 1: (2, 0)}
    assert any(v.startswith("X1") for v in check_timetable(inst, tt, Extras(max_per_day=(1, 3))))
    assert any(v.startswith("X2") for v in check_timetable(inst, tt, Extras(unavailable=frozenset({(0, 2)}))))
    assert any(v.startswith("X3") for v in check_timetable(inst, tt, Extras(invigilators=(1, 1))))
    assert any(v.startswith("X4") for v in check_timetable(inst, tt, Extras(min_gap=3)))
    assert any(v.startswith("X5") for v in check_timetable(inst, tt, Extras(large_early=(1, 1))))


# ---- every model against brute force (550 random tiny instances) --------------

@pytest.mark.parametrize("seed", range(6))
def test_models_agree_with_brute_force_main(seed):
    """6 seeds x 50 tiny instances: sat/unsat matches brute force (C1-C5 only)."""
    rng = random.Random(seed)
    for _ in range(50):
        inst = tiny_instance(rng)
        truth = "sat" if brute_force(inst) else "unsat"
        for model in MODELS:
            res = solve(inst, model)
            assert res.status == truth, (model, vars(inst))
            if res.timetable is not None:
                assert check_timetable(inst, res.timetable) == []


@pytest.mark.parametrize("seed", range(100, 105))
def test_models_agree_with_brute_force_extras(seed):
    """5 seeds x 50 tiny instances, each with a random mix of X1-X5 switched on."""
    rng = random.Random(seed)
    for _ in range(50):
        inst = tiny_instance(rng)
        extras = random_extras(rng, inst)
        truth = "sat" if brute_force(inst, extras) else "unsat"
        for model in MODELS:
            res = solve(inst, model, extras)
            assert res.status == truth, (model, vars(inst), extras)
            if res.timetable is not None:
                assert check_timetable(inst, res.timetable, extras) == []


def test_at_most_clauses_mean_weighted_at_most():
    """The cnf helper: a True/False assignment passes the clauses exactly when the
    weighted count of True literals is at most k."""
    rng = random.Random(3)
    for _ in range(40):
        n, k = rng.randint(1, 5), rng.randint(0, 4)
        weights = [rng.randint(1, 3) for _ in range(n)]
        lits = [z3.Bool(f"v{i}") for i in range(n)]
        clauses = at_most(lits, k, weights)
        for values in product([False, True], repeat=n):
            sub = [(v, z3.BoolVal(b)) for v, b in zip(lits, values)]
            holds = all(z3.is_true(z3.simplify(z3.substitute(c, *sub))) for c in clauses)
            assert holds == (sum(w for w, b in zip(weights, values) if b) <= k)


# ---- counting, explanations, optimisation ---------------------------------------

@pytest.mark.parametrize("model", MODELS)
def test_counts_match_brute_force(model):
    """--count finds exactly the same set of timetables as brute force."""
    rng = random.Random(7)
    for _ in range(25):
        inst = tiny_instance(rng)
        extras = random_extras(rng, inst)
        found, exact = count_timetables(inst, model, extras, cap=10_000)
        assert exact
        assert sorted(map(as_sorted, found)) == sorted(map(as_sorted, brute_force(inst, extras)))


@pytest.mark.parametrize("model", MODELS)
def test_count_cap_and_supplied_counts(model):
    """Known counts on supplied files, and the "at least" result when capped."""
    found, exact = count_timetables(load("sat8.txt"), model, cap=10_000)
    assert exact and len(found) == 162
    found, exact = count_timetables(load("sat1.txt"), model, cap=5)
    assert exact and len(found) == 1
    found, exact = count_timetables(load("sat6.txt"), model, cap=3)
    assert len(found) == 3 and not exact


@pytest.mark.parametrize("model", MODELS)
def test_explain_gives_a_minimal_unsat_core(model):
    """--explain returns a clash that is really unsat and minimal: removing any
    one group from it makes it sat."""
    assert explain_unsat(load("unsat1.txt"), model) == ["C1", "C3"]
    assert {"C4", "C5"} <= set(explain_unsat(load("unsat5.txt"), model))
    assert explain_unsat(load("sat3.txt"), model) is None
    for path in INSTANCES:
        if expected(path) == "unsat":
            inst = read_file(path)
            core = explain_unsat(inst, model)
            groups, _, _ = MODELS[model](inst, NO_EXTRAS)
            for drop in [None] + core:  # the core is unsat; without any one group it is sat
                s = z3.SolverFor("QF_FD") if drop is None else z3.Solver()
                for g in core:
                    if g != drop:
                        s.add(groups[g])
                assert s.check() == (z3.unsat if drop is None else z3.sat), (path, core, drop)


@pytest.mark.parametrize("model", MODELS)
def test_optimise_matches_brute_force(model):
    """--optimize makespan / gap reach the same best value as brute force."""
    rng = random.Random(11)
    for _ in range(20):
        inst = tiny_instance(rng)
        sols = brute_force(inst)
        status, tt, value = optimise(inst, "makespan", model)
        assert status == ("sat" if sols else "unsat")
        if not sols:
            continue
        assert check_timetable(inst, tt) == []
        if inst.number_of_exams:
            assert value == min(max(t for t, _ in s.values()) for s in sols)
        _, _, pairs = get_student_data(inst)
        status, tt, gap = optimise(inst, "gap", model)
        assert check_timetable(inst, tt) == []
        if pairs:
            assert gap == max(min(abs(s[a][0] - s[b][0]) for a, b in pairs) for s in sols)


# ---- input, edge cases, command line ----------------------------------------------

def test_reader_allows_blank_lines_and_spaces(tmp_path):
    f = tmp_path / "i.txt"
    f.write_text("Number of students: 2 \nNumber of exams: 1\nNumber of slots: 1\r\n"
                 "Number of rooms: 1\nRoom 0 capacity: 2\n\n0 0\t\n0 1\n0 1\n\n")
    inst = read_file(str(f))
    assert get_student_data(inst)[0] == [2]  # the repeated line is counted once
    assert solve(inst).status == "sat"


def test_out_of_range_enrolment_rejected(tmp_path):
    """An enrolment for exam 3 when there is only 1 exam must raise ValueError."""
    f = tmp_path / "bad.txt"
    f.write_text("Number of students: 1\nNumber of exams: 1\nNumber of slots: 1\n"
                 "Number of rooms: 1\nRoom 0 capacity: 1\n3 0\n")
    with pytest.raises(ValueError):
        read_file(str(f))


@pytest.mark.parametrize("model", MODELS)
def test_degenerate_instances(model):
    """No exams -> sat; exams but no slots, or no rooms -> unsat."""
    assert solve(random_instance(3, 0, 0, 0, seed=1), model).status == "sat"
    assert solve(random_instance(3, 2, 0, 2, seed=1), model).status == "unsat"
    assert solve(random_instance(3, 2, 3, 0, seed=1), model).status == "unsat"


def test_generated_file_round_trip(tmp_path):
    """write_instance then read_file gives back the same instance."""
    inst = random_instance(10, 4, 5, 2, seed=3)
    path = tmp_path / "g.txt"
    write_instance(inst, str(path))
    back = read_file(str(path))
    assert back.exams_to_students == inst.exams_to_students
    assert back.room_capacities == inst.room_capacities


def test_default_output_format(capsys):
    """Default run: 'sat', the timetable, the time in ms - nothing else."""
    assert main([os.path.join(HERE, "inst", "sat3.txt")]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert lines[0] == "sat" and lines[-1].startswith("Time:") and "ms" in lines[-1]
    assert len(lines) == 1 + 2 + 2 + 1  # status, table header (2 lines), 2 exams, time
    main([os.path.join(HERE, "inst", "unsat2.txt")])
    lines = capsys.readouterr().out.splitlines()
    assert lines[0] == "unsat" and len(lines) == 2


def test_cli_analysis_output(capsys):
    """--check / --count / --explain print their extra lines."""
    assert main([os.path.join(HERE, "inst", "sat1.txt"), "--check", "--count", "5"]) == 0
    out = capsys.readouterr().out
    assert "Checker: OK" in out and "exactly 1" in out
    main([os.path.join(HERE, "inst", "unsat1.txt"), "--explain", "--model", "cnf"])
    lines = capsys.readouterr().out.splitlines()
    assert lines[0] == "unsat" and any("C3" in line for line in lines)


@pytest.mark.parametrize("model", MODELS)
def test_cli_extra_constraint_flags(model, capsys):
    """All five extra-constraint flags together, plus --optimize, never give a
    timetable that the checker rejects."""
    path = os.path.join(HERE, "inst", "sat10.txt")
    main([path, "--model", model, "--check", "--max-per-day", "1", "3", "--unavailable", "1:0",
          "--invigilators", "3", "10", "--min-gap", "2", "--large-early", "20", "5",
          "--optimize", "gap"])
    out = capsys.readouterr().out
    assert out.splitlines()[0] in {"sat", "unsat"}
    assert "FAILED" not in out

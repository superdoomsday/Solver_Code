# Exam Timetabling Solver (Z3) - COMP3070 CW1

## 1. What this solver does

Given a file describing students, exams, time slots and rooms, the solver
uses the Z3 solver to decide whether every exam can be given **one slot and
one room** so that all five main rules hold:

| Rule | Meaning |
|---|---|
| C1 | each exam is in exactly one slot and one room |
| C2 | a room holds at most one exam per slot |
| C3 | the room is big enough for the exam's students |
| C4 | no student has exams in two consecutive slots |
| C5 | no student has two exams in the same slot |

It prints `sat` and a timetable if one exists, or `unsat` if none does,
followed by the time taken. Five optional extra rules (X1-X5) and some
analysis tools (checking, counting, explaining, optimising) are available
through command-line options.

## 2. Files

| File / folder | What it is |
|---|---|
| `cw1_solver.py` | The solver. **This is the file you run.** |
| `inst/` | The 20 supplied instances (`sat1.txt` ... `sat10.txt`, `unsat1.txt` ... `unsat10.txt`) |
| `tests/` | Automated tests (pytest) |
| `benchmark.py` | Timing experiments used in the report (writes to `results/`) |
| `gen_instances.py` | Random instance generator and brute-force checker (used by tests and benchmark) |
| `results/` | CSV files and charts produced by `benchmark.py` |
| `requirements.txt` | Python packages needed |

## 3. Setup

You need **Python 3.8 or newer**. All commands below are run from inside the
`Solver_Code` folder.

**Mac / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

**Windows (PowerShell)**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

(Using a virtual environment, `.venv`, is optional but keeps these packages
separate from the rest of your computer.) The solver itself only needs
`z3-solver`. `pytest` is for the tests, `matplotlib` for the benchmark charts,
and `ortools` is optional (only for the CP-SAT comparison in `benchmark.py`).

## 4. Basic use

```
python cw1_solver.py <instance file(s)> [options]
```

**A satisfiable instance**

```
$ python cw1_solver.py inst/sat1.txt
sat
 Exam | Slot | Room | Students | Capacity
------+------+------+----------+---------
    0 |    0 |    0 |        3 |        3
Time: 1.68 ms (build 0.75 ms + solve 0.93 ms, model int)
```

Each row says which slot and room an exam got, how many students take it,
and the room's capacity. *Build* is the time to create the Z3 constraints,
*solve* is the time Z3 needs to find the answer.

**An unsatisfiable instance**

```
$ python cw1_solver.py inst/unsat1.txt
unsat
Time: 1.53 ms (build 0.74 ms + solve 0.79 ms, model int)
```

**Several files, or all of them at once**

```
$ python cw1_solver.py inst/*.txt
== inst/sat1.txt
sat
 Exam | Slot | Room | Students | Capacity
------+------+------+----------+---------
    0 |    0 |    0 |        3 |        3
Time: 1.45 ms (build 0.68 ms + solve 0.77 ms, model int)

== inst/sat10.txt
sat
...
== inst/unsat10.txt
unsat
Time: 24.14 ms (build 5.22 ms + solve 18.92 ms, model int)
```

Each file gets a `== file name` header. `inst/*.txt` works on Mac, Linux
**and Windows** (PowerShell and Command Prompt), because the solver expands
the `*` itself. Files are listed in text order (`sat1`, `sat10`, `sat2`, ...).

> Note: times change from run to run, and when several timetables are valid
> Z3 may pick a different one each time. Every one printed is valid.

## 5. Choosing a model (`--model`)

The same problem is written in three different ways ("formulations"). All
three always give the same sat/unsat answer; they differ in speed and style.

| Option | Idea | Default |
|---|---|---|
| `--model int` | each exam has one whole-number slot and one whole-number room | yes |
| `--model bool` | True/False tables: "exam e is in slot t", "exam e is in room r" | |
| `--model cnf` | the same True/False tables, but every rule written as plain OR-clauses (the form a SAT solver uses) | |

```
$ python cw1_solver.py inst/sat3.txt --model bool
sat
 Exam | Slot | Room | Students | Capacity
------+------+------+----------+---------
    0 |    0 |    0 |        2 |        2
    1 |    1 |    0 |        1 |        2
Time: 1.71 ms (build 1.18 ms + solve 0.53 ms, model bool)
```

## 6. All options

This is the real `--help` output:

```
$ python cw1_solver.py --help
usage: cw1_solver.py [-h] [--model {int,bool,cnf}] [--check] [--count CAP]
                     [--explain] [--optimize {gap,makespan}] [--timeout MS]
                     [--max-per-day K D] [--unavailable R:T]
                     [--invigilators N Q] [--min-gap G] [--large-early N K]
                     files [files ...]

Z3 exam timetabling solver

positional arguments:
  files                 instance file(s)

options:
  -h, --help            show this help message and exit
  --model {int,bool,cnf}
                        formulation (default int)
  --check               re-check the timetable without Z3
  --count CAP           count up to CAP timetables
  --explain             for unsat: which constraint groups clash
  --optimize {gap,makespan}
                        find a best timetable
  --timeout MS          Z3 timeout in ms

extra constraints (all OFF by default):
  --max-per-day K D     X1: at most K exams per student per day of D slots
  --unavailable R:T     X2: room R closed in slot T (repeatable)
  --invigilators N Q    X3: N invigilators per slot, one per Q students
  --min-gap G           X4: a student's exams at least G slots apart
  --large-early N K     X5: exams with >= N students in the first K slots
```

Options can be combined freely, e.g. `--model cnf --check --count 10`.

### `--check`: double-check the timetable

Re-checks the timetable with plain Python code that does not use Z3 at all,
so it is an independent second opinion. It checks C1-C5 plus any extra
constraints you switched on.

```
$ python cw1_solver.py inst/sat1.txt --check
sat
 Exam | Slot | Room | Students | Capacity
------+------+------+----------+---------
    0 |    0 |    0 |        3 |        3
Time: 1.91 ms (build 0.90 ms + solve 1.01 ms, model int)
Checker: OK, all active constraints hold
```

Check all 20 files with each model:

```
python cw1_solver.py inst/*.txt --check
python cw1_solver.py inst/*.txt --model bool --check
python cw1_solver.py inst/*.txt --model cnf --check
```

### `--count CAP`: how many timetables are there?

Finds up to `CAP` different valid timetables. It says *exactly* N if it found
them all, or *at least* N if it stopped at the cap.

```
$ python cw1_solver.py inst/sat8.txt --count 1000
...
Solutions: exactly 162 timetable(s) (86.2 ms)

$ python cw1_solver.py inst/sat6.txt --count 100
...
Solutions: at least 100 timetable(s) (60.3 ms)
```

### `--explain`: why is it unsat?

For an unsat instance, prints the smallest set of rule groups that cannot all
hold together (removing any one of them would make it solvable).

```
$ python cw1_solver.py inst/unsat1.txt --explain
unsat
Time: 5.69 ms (build 1.85 ms + solve 3.84 ms, model int)
Explanation: smallest set of clashing constraints:
  C1: each exam in exactly one slot and one room
  C3: room capacity
```

Here the exam is too big for every room (C3), but it must go in some room (C1).

```
$ python cw1_solver.py inst/unsat5.txt --explain
unsat
Time: 6.26 ms (build 2.49 ms + solve 3.77 ms, model int)
Explanation: smallest set of clashing constraints:
  C1: each exam in exactly one slot and one room
  C4: no consecutive exams for a student
  C5: no two exams in the same slot for a student
```

### `--optimize gap` / `--optimize makespan`: find the best timetable

First prints the normal answer, then a best timetable:

- `gap`: make the **smallest gap between any student's two exams as large as
  possible** (spreads each student's exams out).
- `makespan`: make the **last slot used as early as possible** (packs the
  timetable into fewer slots).

```
$ python cw1_solver.py inst/sat10.txt --optimize gap
sat
...
Optimum (largest smallest gap between a student's exams): 2
 Exam | Slot | Room | Students | Capacity
------+------+------+----------+---------
    2 |    0 |    0 |       13 |       13
    1 |    2 |    1 |       20 |       27
    4 |    4 |    1 |       19 |       27
    5 |    4 |    2 |        1 |        4
    0 |    6 |    1 |       23 |       27
    3 |    8 |    0 |        2 |       13

$ python cw1_solver.py inst/sat10.txt --optimize makespan
sat
...
Optimum (smallest last slot used): 8
 Exam | Slot | Room | Students | Capacity
------+------+------+----------+---------
    2 |    0 |    0 |       13 |       13
    1 |    2 |    1 |       20 |       27
    0 |    4 |    1 |       23 |       27
    5 |    4 |    2 |        1 |        4
    3 |    6 |    3 |        2 |       10
    4 |    8 |    1 |       19 |       27
```

(`...` marks the first timetable, left out here to save space.)

### `--timeout MS`: time limit

Stops Z3 after `MS` milliseconds; if it has not finished, the status is
`unknown`. Useful for very large instances.

```
python cw1_solver.py inst/sat10.txt --timeout 5000
```

## 7. The five additional constraints (X1-X5)

**They are all OFF by default.** A plain run solves exactly the coursework
problem (C1-C5), which is what the supplied and unseen instances are labelled
and marked with; switching an extra on can turn a `sat` instance into `unsat`.
Switch one on by adding its flag. Every model (`int`, `bool`, `cnf`) supports
all five, and `--check` and `--explain` understand them too.

All examples use `inst/sat10.txt` (6 exams, 10 slots, 5 rooms), except X4.
Without any extras its default timetable looks like this:

```
$ python cw1_solver.py inst/sat10.txt
sat
 Exam | Slot | Room | Students | Capacity
------+------+------+----------+---------
    0 |    0 |    1 |       23 |       27
    3 |    2 |    1 |        2 |       27
    1 |    4 |    1 |       20 |       27
    5 |    6 |    0 |        1 |       13
    2 |    7 |    0 |       13 |       13
    4 |    9 |    1 |       19 |       27
```

### X1 - Max exams per student per day: `--max-per-day K D`

The slots are split into "days" of `D` slots each (slots 0..D-1 are day 0,
D..2D-1 are day 1, and so on). No student may have more than `K` exams on
one day. `K` and `D` must be at least 1.

```
$ python cw1_solver.py inst/sat10.txt --max-per-day 2 5 --check
sat
 Exam | Slot | Room | Students | Capacity
------+------+------+----------+---------
    3 |    0 |    2 |        2 |        4
    1 |    2 |    1 |       20 |       27
    2 |    4 |    0 |       13 |       13
    0 |    6 |    1 |       23 |       27
    4 |    8 |    1 |       19 |       27
    5 |    9 |    1 |        1 |       27
Time: 19.61 ms (build 13.76 ms + solve 5.85 ms, model int)
Checker: OK, all active constraints hold
```

Days are slots 0-4 and 5-9, and no student has more than 2 exams in either.
Making it too strict gives `unsat`, and `--explain` names X1 as the cause:

```
$ python cw1_solver.py inst/sat10.txt --max-per-day 1 3 --explain
unsat
Time: 34.68 ms (build 29.05 ms + solve 5.63 ms, model int)
Explanation: smallest set of clashing constraints:
  C1: each exam in exactly one slot and one room
  X1: max exams per student per day
```

### X2 - Room unavailable: `--unavailable R:T`

Room `R` is closed in slot `T` (written as `ROOM:SLOT`, no spaces). Repeat
the flag to close more room/slot pairs.

```
$ python cw1_solver.py inst/sat10.txt --unavailable 1:0 --unavailable 1:2 --check
sat
 Exam | Slot | Room | Students | Capacity
------+------+------+----------+---------
    5 |    1 |    0 |        1 |       13
    4 |    1 |    1 |       19 |       27
    0 |    3 |    1 |       23 |       27
    3 |    5 |    0 |        2 |       13
    1 |    7 |    1 |       20 |       27
    2 |    9 |    0 |       13 |       13
Time: 7.49 ms (build 3.49 ms + solve 4.00 ms, model int)
Checker: OK, all active constraints hold
```

By default exam 0 used room 1 in slot 0. Now room 1 is never used in slots 0
or 2.

### X3 - Invigilator limit: `--invigilators N Q`

Each slot has `N` invigilators, and an exam needs one invigilator per `Q`
students (rounded up, at least 1). The exams in one slot may not need more
than `N` in total. `N` must be at least 0 and `Q` at least 1.

```
$ python cw1_solver.py inst/sat10.txt --invigilators 3 10 --check
sat
 Exam | Slot | Room | Students | Capacity
------+------+------+----------+---------
    1 |    0 |    1 |       20 |       27
    0 |    2 |    1 |       23 |       27
    4 |    4 |    1 |       19 |       27
    5 |    6 |    0 |        1 |       13
    3 |    6 |    1 |        2 |       27
    2 |    8 |    0 |       13 |       13
Time: 27.95 ms (build 8.47 ms + solve 19.48 ms, model int)
Checker: OK, all active constraints hold
```

Exam 0 (23 students) needs 3 invigilators, so it must have a slot to itself;
exams 5 and 3 need 1 each and can share slot 6. With only 2 invigilators,
exam 0 can never be held:

```
$ python cw1_solver.py inst/sat10.txt --invigilators 2 10 --explain
unsat
Time: 10.75 ms (build 5.79 ms + solve 4.97 ms, model int)
Explanation: smallest set of clashing constraints:
  C1: each exam in exactly one slot and one room
  X3: invigilator limit per slot
```

### X4 - Minimum gap between a student's exams: `--min-gap G`

Two exams that share a student must be at least `G` slots apart. C4 + C5
already force a gap of 2, so `G = 3` or more makes it stricter. `G` must be
at least 1.

```
$ python cw1_solver.py inst/sat6.txt --min-gap 3 --check
sat
 Exam | Slot | Room | Students | Capacity
------+------+------+----------+---------
    0 |    0 |    0 |        6 |       11
    2 |    0 |    1 |        2 |       12
    1 |    3 |    0 |        9 |       11
Time: 4.78 ms (build 1.76 ms + solve 3.02 ms, model int)
Checker: OK, all active constraints hold
```

Exam 1 shares students with exams 0 and 2. It is now 3 slots away from
both of them (without X4 the three exams were in slots 0, 2 and 4, only 2
apart). On `sat10.txt` a gap of 4 is impossible:

```
$ python cw1_solver.py inst/sat10.txt --min-gap 4 --explain
unsat
Time: 12.34 ms (build 6.47 ms + solve 5.87 ms, model int)
Explanation: smallest set of clashing constraints:
  C1: each exam in exactly one slot and one room
  X4: minimum gap between a student's exams
```

### X5 - Large exams early: `--large-early N K`

Every exam with at least `N` students must be in one of the first `K` slots
(slots 0 to K-1), e.g. so big exams can be marked first. `K` must be at
least 0.

```
$ python cw1_solver.py inst/sat10.txt --large-early 15 5 --check
sat
 Exam | Slot | Room | Students | Capacity
------+------+------+----------+---------
    0 |    0 |    1 |       23 |       27
    1 |    2 |    1 |       20 |       27
    4 |    4 |    1 |       19 |       27
    2 |    6 |    0 |       13 |       13
    3 |    8 |    0 |        2 |       13
    5 |    9 |    2 |        1 |        4
Time: 16.10 ms (build 4.67 ms + solve 11.43 ms, model int)
Checker: OK, all active constraints hold
```

Exams 0, 1 and 4 (15+ students) are now all in slots 0-4. Exam 4 was in
slot 9 by default.

### Combining several extras

Just add several flags. All of them must hold at the same time:

```
$ python cw1_solver.py inst/sat10.txt --max-per-day 2 3 --unavailable 1:0 --invigilators 3 10 --large-early 20 5 --check
sat
 Exam | Slot | Room | Students | Capacity
------+------+------+----------+---------
    5 |    0 |    0 |        1 |       13
    0 |    1 |    1 |       23 |       27
    1 |    3 |    1 |       20 |       27
    4 |    5 |    1 |       19 |       27
    2 |    7 |    0 |       13 |       13
    3 |    9 |    0 |        2 |       13
Time: 33.25 ms (build 26.55 ms + solve 6.70 ms, model int)
Checker: OK, all active constraints hold
```

The same flags work with `--model bool` or `--model cnf`, and with
`--count`, `--explain` and `--optimize`. If a combination is `unsat`, add
`--explain` to see which rules clash:

```
$ python cw1_solver.py inst/sat10.txt --unavailable 1:0 --invigilators 3 10 --large-early 15 5 --min-gap 3 --explain
unsat
Time: 12.45 ms (build 6.78 ms + solve 5.67 ms, model int)
Explanation: smallest set of clashing constraints:
  C1: each exam in exactly one slot and one room
  X4: minimum gap between a student's exams
```

A bad value is rejected with a clear message, for example:

```
$ python cw1_solver.py inst/sat10.txt --min-gap 0
...
cw1_solver.py: error: --min-gap needs G >= 1
```

## 8. Running the tests

```
python -m pytest tests -q
```

Expected result (takes about 10 seconds):

```
103 passed in 8.62s
```

The tests check that all 20 supplied instances give their labelled answer
under every model, that the checker catches each broken rule, and that every
model agrees with brute-force search on 550 small random instances (with and
without the extra constraints), including `--count`, `--explain` and
`--optimize`.

## 9. Benchmark and instance generator

`benchmark.py` re-runs the timing experiments from the report and **overwrites
the files in `results/`**. It needs `matplotlib`; `ortools` is optional.

```
python benchmark.py --quick    # small version, about 20 seconds
python benchmark.py            # full version, several minutes
```

`gen_instances.py` has no command line of its own; use it from Python to make
a random instance file (students, exams, slots, rooms, room capacity range,
seed):

```
$ python -c "from gen_instances import random_instance, write_instance; write_instance(random_instance(30, 8, 12, 3, capacity=(5, 25), seed=42), 'my_instance.txt')"
$ python cw1_solver.py my_instance.txt --check
sat
 Exam | Slot | Room | Students | Capacity
------+------+------+----------+---------
    3 |    0 |    0 |        7 |       25
    1 |    2 |    0 |       11 |       25
    0 |    4 |    0 |        5 |       25
    2 |    4 |    1 |        5 |        8
    4 |    6 |    0 |       10 |       25
    5 |    8 |    0 |        8 |       25
    7 |   10 |    1 |        3 |        8
    6 |   11 |    0 |        9 |       25
Time: 9.39 ms (build 4.20 ms + solve 5.19 ms, model int)
Checker: OK, all active constraints hold
```

## 10. Input file format

Header lines first, then one `exam student` pair per line (everything is
numbered from 0). Example, `inst/sat3.txt`:

```
Number of students: 3
Number of exams: 2
Number of slots: 2
Number of rooms: 1
Room 0 capacity: 2
0 0
0 1
1 2
```

So exam 0 is taken by students 0 and 1, and exam 1 by student 2. There is one
`Room r capacity:` line per room. Blank lines and extra spaces are allowed; an
exam or student number that is out of range is reported as an error.

## 11. Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError: No module named 'z3'` | Install the packages: `python -m pip install -r requirements.txt` (with your `.venv` activated). Install `z3-solver`, not `z3`. |
| `python` not found (Mac/Linux) | Use `python3` instead of `python`. |
| PowerShell will not run `.venv\Scripts\Activate.ps1` | Run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, or skip activation and use `.venv\Scripts\python cw1_solver.py ...`. |
| `inst/*.txt` gives `No such file or directory` | Make sure you are inside the `Solver_Code` folder. The solver expands `*` itself, so this works in PowerShell too. |
| `FileNotFoundError` for one file | Check the path and spelling, e.g. `inst/sat1.txt`. |
| `error: --min-gap needs G >= 1` (or similar) | An extra-constraint value is out of range; see section 7 for valid values. |
| `benchmark.py` fails with `No module named 'matplotlib'` | `python -m pip install matplotlib` (it is in `requirements.txt`). |

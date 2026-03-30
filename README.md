# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Smarter Scheduling

The `Scheduler` class was extended with four algorithmic features beyond the baseline greedy planner:

**Sorting by time**
`sort_by_time(ascending)` orders scheduled tasks by their `"HH:MM"` start time. A lambda converts each time string to an `(hour, minute)` integer tuple so `sorted()` compares numerically — ensuring `"09:05"` always sorts before `"10:00"` regardless of zero-padding.

**Filtering by pet and status**
`filter_tasks(pet_name, completed)` accepts either or both arguments to narrow the scheduled task list. Pet matching uses object identity (`id()`) so two pets with identically named tasks are never confused. Passing neither argument returns all scheduled tasks unchanged.

**Recurring task overview**
`get_recurring_summary()` maps each day of the week to the tasks that repeat on that day: `"daily"` tasks appear every day, `"weekly"` tasks are pinned to Monday, and `"as needed"` tasks are excluded. This gives the owner a at-a-glance view of their full weekly care load.

**Conflict detection**
`detect_conflicts()` returns a plain list of warning strings — it never raises. It checks for three problems: (1) total pending task time exceeding the daily budget, (2) a single task too long to ever fit, and (3) two or more tasks sharing the same start time. Time-slot conflicts use an O(n) dict-bucket approach and report the pet name alongside each clashing task.

## Testing PawPal+

### Run the test suite

```bash
python -m pytest tests/test_pawpal.py -v
```

`-v` (verbose) prints each test name and PASSED/FAILED individually. Omit it for a one-line summary.

### What the tests cover

The suite contains **37 tests** across eight behavioral groups:

| Group | Tests | What is verified |
|---|---|---|
| `build_schedule` priority & budget | 5 | High-priority tasks win when time is tight; total scheduled time never exceeds the budget; the second-pass bin-packing recovers small tasks that were initially skipped |
| `sort_by_time` | 4 | Tasks added out of order come back in chronological HH:MM order; same-hour tasks are ordered by minute; descending sort works; empty schedule returns `[]` without crashing |
| `filter_tasks` by pet & status | 6 | Pet filtering uses object identity so two pets with the same task name never bleed into each other; unknown pet name returns `[]`; pending/done status filtering works independently and combined |
| `detect_conflicts` | 5 | Same-slot clashes are caught across pets; different-time tasks produce no false positives; the method always returns a list and never raises; budget overload and duplicate descriptions are also warned |
| Edge cases | 6 | Pet with no tasks, owner with no pets, all "as needed" tasks, weekly task pinned to Monday only, invalid time format, zero duration |
| **Sorting correctness** | 3 | Tasks added in reverse order return in strict chronological order; same-hour ordering by minute; descending flag |
| **Recurrence logic** | 4 | Completing a daily task + calling `renew_recurring_tasks()` creates a new pending copy; the renewed copy is a different object; weekly tasks are not auto-renewed; renewed task appears in the next `build_schedule()` run |
| **Conflict detection** | 4 | Same-pet clash, cross-pet clash, no false positives on different times, warning message names both pet owners |

### Confidence level

★★★★☆ — 4 / 5

The core scheduling logic (priority ordering, time budget, sorting, filtering, conflict detection, and recurrence) is fully covered by automated tests and all 37 pass. One star is withheld because the UI layer (`app.py`) has no automated tests — Streamlit interactions are exercised manually only, which leaves the wiring between the UI and `Scheduler` unverified by the suite.

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

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

The scheduler (`Scheduler` in `pawpal_system.py`) goes beyond a simple task list with the following features:

- **Recurring tasks** — tasks carry a `RecurrenceRule` (`DAILY`, `WEEKDAYS`, `WEEKLY`). When a recurring task is marked complete via `Pet.complete_task()`, a new instance is automatically created with the next due date (today + 1 day for daily, next weekday for weekdays, today + 7 days for weekly).

- **Time-of-day bands** — tasks declare a preferred time (`MORNING`, `AFTERNOON`, `EVENING`, `ANY`). The scheduler groups tasks into these bands and assigns consecutive start/end times within each band so the output is a fully time-slotted plan.

- **Priority-based budget fitting** — tasks are sorted by priority (highest first) and added greedily until the owner's available time is exhausted. This guarantees the most critical tasks always make it into the plan.

- **Filtering** — `DailyPlan` exposes `get_walks()`, `get_by_category()`, and `get_incomplete()` to slice the plan by task type or completion status.

- **Conflict detection** — the scheduler detects two kinds of scheduling conflicts and surfaces them as warning messages (no crashes):
  - *Same-pet*: two tasks for one pet overlap in the assigned time window.
  - *Cross-pet*: tasks belonging to different pets overlap, meaning the owner would be double-booked.

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

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, time
from enum import Enum
from typing import Optional


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class TaskCategory(Enum):
    WALK = "walk"
    FEEDING = "feeding"
    MEDICATION = "medication"
    ENRICHMENT = "enrichment"
    GROOMING = "grooming"
    OTHER = "other"


class TimeOfDay(Enum):
    MORNING = "morning"
    AFTERNOON = "afternoon"
    EVENING = "evening"
    ANY = "any"


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

@dataclass
class Task:
    task_id: str
    name: str
    category: TaskCategory
    duration_minutes: int
    priority: int                           # 1 (low) – 5 (high)
    preferred_time: TimeOfDay = TimeOfDay.ANY
    notes: str = ""
    pet: Optional[Pet] = field(default=None, repr=False)  # back-reference to owning pet
    is_complete: bool = False

    def mark_complete(self) -> None:
        self.is_complete = True

    def is_valid(self) -> bool:
        # Valid when: name non-empty, duration > 0, priority in 1–5
        pass


@dataclass
class WalkTask(Task):
    distance_miles: float = 0.0
    route_notes: str = ""


# ---------------------------------------------------------------------------
# Pet
# ---------------------------------------------------------------------------

@dataclass
class Pet:
    name: str
    species: str
    breed: str
    age_years: int
    weight_lbs: float
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        self.tasks.append(task)

    def remove_task(self, task_id: str) -> None:
        pass

    def edit_task(self, task_id: str, updated_task: Task) -> None:
        pass

    def get_tasks(self) -> list[Task]:
        pass


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------

@dataclass
class Owner:
    name: str
    email: str
    time_available_minutes: int
    preferences: str = ""
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        pass

    def get_pets(self) -> list[Pet]:
        pass


# ---------------------------------------------------------------------------
# Plan
# ---------------------------------------------------------------------------

@dataclass
class ScheduledTask:
    task: Task
    start_time: time   # e.g. time(8, 0)
    end_time: time     # e.g. time(8, 30)


@dataclass
class DailyPlan:
    plan_date: date
    pet: Pet
    owner: Owner                            # retained so constraints are always accessible
    scheduled_tasks: list[ScheduledTask] = field(default_factory=list)
    reasoning: str = ""

    @property
    def total_duration_minutes(self) -> int:
        # Computed on the fly so it never goes stale
        pass

    def display_summary(self) -> str:
        pass

    def get_walks(self) -> list[ScheduledTask]:
        pass


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

class Scheduler:
    # No time_budget stored here — read it from the owner to avoid drift

    def generate_plan(self, pet: Pet, owner: Owner) -> DailyPlan:
        pass

    def _prioritize(self, tasks: list[Task]) -> list[Task]:
        pass

    def _select_within_budget(self, tasks: list[Task], budget_minutes: int) -> list[Task]:
        # Selects tasks in priority order until budget is exhausted.
        # Runs after _prioritize so the cut-off is applied to an already-ranked list.
        pass

    def _build_reasoning(self, tasks: list[Task]) -> str:
        pass

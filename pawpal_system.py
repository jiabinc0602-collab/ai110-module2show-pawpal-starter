from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date
from enum import Enum


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
    priority: int                          # 1 (low) – 5 (high)
    preferred_time: TimeOfDay = TimeOfDay.ANY
    notes: str = ""

    def is_valid(self) -> bool:
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
        pass

    def remove_task(self, task_id: str) -> None:
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
    start_time: str   # e.g. "08:00"
    end_time: str     # e.g. "08:30"


@dataclass
class DailyPlan:
    plan_date: date
    pet: Pet
    scheduled_tasks: list[ScheduledTask] = field(default_factory=list)
    reasoning: str = ""
    total_duration_minutes: int = 0

    def display_summary(self) -> str:
        pass

    def get_walks(self) -> list[ScheduledTask]:
        pass


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

class Scheduler:
    def __init__(self, time_budget_minutes: int):
        self.time_budget_minutes = time_budget_minutes

    def generate_plan(self, pet: Pet, owner: Owner) -> DailyPlan:
        pass

    def _prioritize(self, tasks: list[Task]) -> list[Task]:
        pass

    def _fits_in_budget(self, tasks: list[Task]) -> list[Task]:
        pass

    def _build_reasoning(self, tasks: list[Task]) -> str:
        pass

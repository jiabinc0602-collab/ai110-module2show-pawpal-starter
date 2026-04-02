from __future__ import annotations
from dataclasses import dataclass, field, replace
from datetime import date, datetime, time, timedelta
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


class RecurrenceRule(Enum):
    NONE     = "none"
    DAILY    = "daily"
    WEEKDAYS = "weekdays"
    WEEKLY   = "weekly"


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
    recurrence: RecurrenceRule = RecurrenceRule.NONE
    due_date: Optional[date] = None         # None means "today"

    def mark_complete(self) -> Optional[Task]:
        """Mark complete; return the next-occurrence Task if recurring, else None."""
        self.is_complete = True
        base = self.due_date or date.today()
        if self.recurrence == RecurrenceRule.DAILY:
            next_due = base + timedelta(days=1)
        elif self.recurrence == RecurrenceRule.WEEKDAYS:
            delta = 3 if base.weekday() == 4 else 1    # Friday → Monday
            next_due = base + timedelta(days=delta)
        elif self.recurrence == RecurrenceRule.WEEKLY:
            next_due = base + timedelta(weeks=1)
        else:
            return None
        return replace(
            self,
            task_id=f"{self.task_id}_{next_due.isoformat()}",
            is_complete=False,
            due_date=next_due,
        )

    def is_valid(self) -> bool:
        # Valid when: name non-empty, duration > 0, priority in 1–5
        return bool(self.name) and self.duration_minutes > 0 and 1 <= self.priority <= 5


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
        self.tasks = [t for t in self.tasks if t.task_id != task_id]

    def edit_task(self, task_id: str, updated_task: Task) -> None:
        for i, t in enumerate(self.tasks):
            if t.task_id == task_id:
                self.tasks[i] = updated_task
                return

    def complete_task(self, task_id: str) -> None:
        """Mark a task complete and auto-append the next occurrence if it recurs."""
        for task in self.tasks:
            if task.task_id == task_id:
                next_task = task.mark_complete()
                if next_task is not None:
                    self.add_task(next_task)
                return

    def get_tasks(self) -> list[Task]:
        return self.tasks


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
        self.pets.append(pet)

    def get_pets(self) -> list[Pet]:
        return self.pets


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
    warnings: list[str] = field(default_factory=list)

    @property
    def total_duration_minutes(self) -> int:
        """Computed on the fly so it never goes stale."""
        return sum(st.task.duration_minutes for st in self.scheduled_tasks)

    def display_summary(self) -> str:
        """Return a formatted string of the plan sorted by start time."""
        lines = [
            f"Plan for {self.pet.name} — {self.plan_date.strftime('%A, %B %d %Y')}",
            "-" * 52,
        ]
        for st in sorted(self.scheduled_tasks, key=lambda x: x.start_time):
            start  = st.start_time.strftime("%I:%M %p")
            end    = st.end_time.strftime("%I:%M %p")
            status = "x" if st.task.is_complete else " "
            recur  = f" [{st.task.recurrence.value}]" if st.task.recurrence != RecurrenceRule.NONE else ""
            lines.append(f"  [{status}] {start} – {end}  {st.task.name} (P{st.task.priority}){recur}")
        lines.append("-" * 52)
        lines.append(
            f"  Total: {self.total_duration_minutes} min  |  "
            f"Budget: {self.owner.time_available_minutes} min"
        )
        if self.warnings:
            lines.append("")
            for w in self.warnings:
                lines.append(f"  WARNING: {w}")
        return "\n".join(lines)

    def get_walks(self) -> list[ScheduledTask]:
        """Return only walk tasks."""
        return self.get_by_category(TaskCategory.WALK)

    def get_by_category(self, category: TaskCategory) -> list[ScheduledTask]:
        """Return scheduled tasks matching the given category."""
        return [st for st in self.scheduled_tasks if st.task.category == category]

    def get_incomplete(self) -> list[ScheduledTask]:
        """Return only tasks that have not been marked complete."""
        return [st for st in self.scheduled_tasks if not st.task.is_complete]


# ---------------------------------------------------------------------------
# Scheduler internals
# ---------------------------------------------------------------------------

_TIME_ORDER: dict[TimeOfDay, int] = {
    TimeOfDay.MORNING: 0, TimeOfDay.AFTERNOON: 1,
    TimeOfDay.EVENING: 2, TimeOfDay.ANY: 3,
}

_SLOT_START: dict[TimeOfDay, time] = {
    TimeOfDay.MORNING:   time(7, 0),
    TimeOfDay.AFTERNOON: time(12, 0),
    TimeOfDay.EVENING:   time(18, 0),
    TimeOfDay.ANY:       time(9, 0),
}

# Fix 5: stable constant so _assign_times doesn't re-list enum members inline
_BAND_ORDER = [TimeOfDay.MORNING, TimeOfDay.AFTERNOON, TimeOfDay.EVENING, TimeOfDay.ANY]


def _fmt_time_range(start: time, end: time) -> str:
    """Format a start/end time pair as 'HH:MM AM–HH:MM AM' for warning messages."""
    return f"{start.strftime('%I:%M %p')}–{end.strftime('%I:%M %p')}"


def _intervals_overlap(start_a: time, end_a: time, start_b: time, end_b: time) -> bool:
    """Return True if two half-open time intervals [start_a, end_a) and [start_b, end_b) overlap."""
    return start_a < end_b and start_b < end_a


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

class Scheduler:
    # No time_budget stored here — read it from the owner to avoid drift

    def generate_plan(self, pet: Pet, owner: Owner) -> DailyPlan:
        """Build a DailyPlan: expand recurring → prioritize → fit budget → assign times → detect conflicts."""
        today     = date.today()          # Fix 4: compute once, pass to both callers
        tasks     = self._expand_recurring(pet.get_tasks(), today)
        ranked    = self._prioritize(tasks)
        selected  = self._select_within_budget(ranked, owner.time_available_minutes)
        scheduled = self._assign_times(selected, today)
        warnings  = self._detect_overlaps(scheduled, label=pet.name)
        reasoning = self._build_reasoning(selected, owner.time_available_minutes)
        return DailyPlan(
            plan_date=today,
            pet=pet,
            owner=owner,
            scheduled_tasks=scheduled,
            reasoning=reasoning,
            warnings=warnings,
        )

    def generate_all_plans(self, owner: Owner) -> list[DailyPlan]:
        """Generate a plan per pet, then append any cross-pet conflicts to each plan's warnings."""
        plans = [self.generate_plan(pet, owner) for pet in owner.get_pets()]
        cross_warnings = self._detect_cross_pet_overlaps(plans)
        for plan in plans:
            plan.warnings.extend(cross_warnings)
        return plans

    def _prioritize(self, tasks: list[Task]) -> list[Task]:
        """Sort by priority descending, then by time-of-day band (morning first)."""
        return sorted(tasks, key=lambda t: (-t.priority, _TIME_ORDER[t.preferred_time]))

    def _select_within_budget(self, tasks: list[Task], budget_minutes: int) -> list[Task]:
        """Greedy selection: include tasks in priority order until budget is exhausted."""
        selected, total = [], 0
        for task in tasks:
            if total + task.duration_minutes <= budget_minutes:
                selected.append(task)
                total += task.duration_minutes
        return selected

    def _expand_recurring(self, tasks: list[Task], today: date) -> list[Task]:
        """Keep tasks that apply today based on their recurrence rule."""
        result = []
        for task in tasks:
            if task.is_complete:
                continue
            # Fix 3: NONE and DAILY both apply unconditionally — collapsed into one branch
            if task.recurrence in (RecurrenceRule.NONE, RecurrenceRule.DAILY):
                result.append(task)
            elif task.recurrence == RecurrenceRule.WEEKDAYS and today.weekday() < 5:
                result.append(task)
            elif task.recurrence == RecurrenceRule.WEEKLY and today.weekday() == 0:
                result.append(task)
        return result

    def _assign_times(self, tasks: list[Task], today: date) -> list[ScheduledTask]:
        """Assign consecutive start/end times within each time-of-day band."""
        bands: dict[TimeOfDay, list[Task]] = {tod: [] for tod in TimeOfDay}
        for task in tasks:
            bands[task.preferred_time].append(task)

        scheduled = []
        for band in _BAND_ORDER:                        # Fix 5: use constant, not inline list
            cursor = datetime.combine(today, _SLOT_START[band])
            for task in bands[band]:
                start   = cursor.time()
                cursor += timedelta(minutes=task.duration_minutes)
                scheduled.append(ScheduledTask(task=task, start_time=start, end_time=cursor.time()))
        return scheduled

    def _detect_overlaps(self, scheduled: list[ScheduledTask], label: str = "") -> list[str]:
        """Return warning strings for any same-pet time-window overlaps."""
        prefix   = f"[{label}] " if label else ""
        warnings = []
        for i, a in enumerate(scheduled):
            for b in scheduled[i + 1:]:
                if _intervals_overlap(a.start_time, a.end_time, b.start_time, b.end_time):  # Fix 1
                    warnings.append(
                        f"{prefix}'{a.task.name}' ({_fmt_time_range(a.start_time, a.end_time)}) "
                        f"overlaps '{b.task.name}' ({_fmt_time_range(b.start_time, b.end_time)})"
                    )
        return warnings

    def _detect_cross_pet_overlaps(self, plans: list[DailyPlan]) -> list[str]:
        """Return warning strings for tasks across different pets that overlap in time."""
        warnings = []
        for i, plan_a in enumerate(plans):
            for plan_b in plans[i + 1:]:
                for st_a in plan_a.scheduled_tasks:
                    for st_b in plan_b.scheduled_tasks:
                        if _intervals_overlap(st_a.start_time, st_a.end_time, st_b.start_time, st_b.end_time):  # Fix 1
                            warnings.append(
                                f"[Cross-pet] {plan_a.pet.name}:'{st_a.task.name}' "
                                f"({_fmt_time_range(st_a.start_time, st_a.end_time)}) "
                                f"overlaps {plan_b.pet.name}:'{st_b.task.name}' "
                                f"({_fmt_time_range(st_b.start_time, st_b.end_time)})"
                            )
        return warnings

    def _build_reasoning(self, tasks: list[Task], budget: int) -> str:
        """Summarise chosen tasks and how much of the budget they consume."""
        total = sum(t.duration_minutes for t in tasks)
        lines = [
            f"Selected {len(tasks)} task(s) using {total}/{budget} min.",
            "Tasks chosen in priority order:",
        ]
        for t in tasks:
            recur = f" [{t.recurrence.value}]" if t.recurrence != RecurrenceRule.NONE else ""
            lines.append(f"  P{t.priority} — {t.name} ({t.duration_minutes} min){recur}")
        return "\n".join(lines)

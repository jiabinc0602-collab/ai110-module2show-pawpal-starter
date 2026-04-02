from datetime import date, time, timedelta

from pawpal_system import (
    Owner, Pet, Task, TaskCategory, TimeOfDay, RecurrenceRule,
    ScheduledTask, DailyPlan, Scheduler,
    _intervals_overlap,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_task(task_id="t1", priority=3, recurrence=RecurrenceRule.NONE,
              category=TaskCategory.OTHER, duration=15,
              preferred_time=TimeOfDay.ANY):
    """Return a minimal Task instance for use in tests."""
    return Task(
        task_id=task_id,
        name="Test Task",
        category=category,
        duration_minutes=duration,
        priority=priority,
        preferred_time=preferred_time,
        recurrence=recurrence,
    )


def make_pet():
    """Return a minimal Pet instance for use in tests."""
    return Pet(name="Buddy", species="Dog", breed="Labrador", age_years=3, weight_lbs=60.0)


def make_owner(budget=120):
    """Return a minimal Owner instance for use in tests."""
    return Owner(name="Alex", email="a@example.com", time_available_minutes=budget)


def make_scheduled(task, start_h, start_m, end_h, end_m):
    """Wrap a Task in a ScheduledTask with explicit start/end times."""
    return ScheduledTask(task=task, start_time=time(start_h, start_m), end_time=time(end_h, end_m))


# ---------------------------------------------------------------------------
# Task Completion Tests
# ---------------------------------------------------------------------------

class TestMarkComplete:
    def test_task_starts_incomplete(self):
        """A newly created task should default to is_complete=False."""
        task = make_task()
        assert task.is_complete is False

    def test_mark_complete_sets_flag(self):
        """Calling mark_complete() should set is_complete to True."""
        task = make_task()
        task.mark_complete()
        assert task.is_complete is True

    def test_mark_complete_is_idempotent(self):
        """Calling mark_complete() twice should leave is_complete as True."""
        task = make_task()
        task.mark_complete()
        task.mark_complete()
        assert task.is_complete is True


# ---------------------------------------------------------------------------
# Task Addition Tests
# ---------------------------------------------------------------------------

class TestAddTask:
    def test_new_pet_has_no_tasks(self):
        """A freshly created pet should have an empty task list."""
        pet = make_pet()
        assert len(pet.tasks) == 0

    def test_add_task_increases_count(self):
        """Adding one task should raise the pet's task count to 1."""
        pet = make_pet()
        pet.add_task(make_task("t1"))
        assert len(pet.tasks) == 1

    def test_add_multiple_tasks_increases_count(self):
        """Adding two tasks should raise the pet's task count to 2."""
        pet = make_pet()
        pet.add_task(make_task("t1"))
        pet.add_task(make_task("t2"))
        assert len(pet.tasks) == 2

    def test_added_task_is_retrievable(self):
        """The exact task object passed to add_task() should be stored in the list."""
        pet = make_pet()
        task = make_task("t1")
        pet.add_task(task)
        assert pet.tasks[0] is task


# ---------------------------------------------------------------------------
# Recurrence Logic Tests
# ---------------------------------------------------------------------------

class TestRecurrenceLogic:
    def test_daily_task_next_due_is_tomorrow(self):
        """Completing a DAILY task should produce a next occurrence due tomorrow."""
        today = date.today()
        task = make_task(recurrence=RecurrenceRule.DAILY)
        task.due_date = today
        next_task = task.mark_complete()
        assert next_task is not None
        assert next_task.due_date == today + timedelta(days=1)

    def test_daily_task_next_occurrence_is_incomplete(self):
        """The next occurrence created from a DAILY task must start as incomplete."""
        task = make_task(recurrence=RecurrenceRule.DAILY)
        next_task = task.mark_complete()
        assert next_task.is_complete is False

    def test_weekly_task_next_due_is_seven_days(self):
        """Completing a WEEKLY task should produce a next occurrence due 7 days later."""
        today = date.today()
        task = make_task(recurrence=RecurrenceRule.WEEKLY)
        task.due_date = today
        next_task = task.mark_complete()
        assert next_task is not None
        assert next_task.due_date == today + timedelta(weeks=1)

    def test_weekdays_task_on_friday_next_due_is_monday(self):
        """Completing a WEEKDAYS task on Friday should skip the weekend to Monday."""
        friday = date(2026, 4, 3)          # known Friday
        task = make_task(recurrence=RecurrenceRule.WEEKDAYS)
        task.due_date = friday
        next_task = task.mark_complete()
        assert next_task is not None
        assert next_task.due_date == date(2026, 4, 6)   # Monday

    def test_weekdays_task_on_weekday_next_due_is_next_day(self):
        """Completing a WEEKDAYS task on a non-Friday weekday should produce the next day."""
        monday = date(2026, 3, 30)
        task = make_task(recurrence=RecurrenceRule.WEEKDAYS)
        task.due_date = monday
        next_task = task.mark_complete()
        assert next_task.due_date == date(2026, 3, 31)

    def test_none_task_returns_no_next_occurrence(self):
        """Completing a non-recurring task must return None, not a new task."""
        task = make_task(recurrence=RecurrenceRule.NONE)
        next_task = task.mark_complete()
        assert next_task is None

    def test_complete_task_appends_next_occurrence_to_pet(self):
        """Pet.complete_task() should auto-append the next occurrence for a DAILY task."""
        pet = make_pet()
        pet.add_task(make_task("t1", recurrence=RecurrenceRule.DAILY))
        pet.complete_task("t1")
        assert len(pet.tasks) == 2

    def test_complete_none_task_does_not_grow_pet_list(self):
        """Pet.complete_task() on a non-recurring task must not append anything."""
        pet = make_pet()
        pet.add_task(make_task("t1", recurrence=RecurrenceRule.NONE))
        pet.complete_task("t1")
        assert len(pet.tasks) == 1

    def test_complete_nonexistent_task_id_is_safe(self):
        """Pet.complete_task() with an unknown id must not crash or modify the list."""
        pet = make_pet()
        pet.add_task(make_task("t1"))
        pet.complete_task("does-not-exist")
        assert len(pet.tasks) == 1


# ---------------------------------------------------------------------------
# Sorting Correctness Tests
# ---------------------------------------------------------------------------

class TestSortingCorrectness:
    def _plan_with_tasks(self, tasks, owner=None):
        """Build a DailyPlan directly from a list of ScheduledTasks."""
        pet = make_pet()
        owner = owner or make_owner()
        return DailyPlan(
            plan_date=date.today(), pet=pet, owner=owner,
            scheduled_tasks=tasks,
        )

    def test_display_summary_is_chronological(self):
        """display_summary() must list tasks in start_time order regardless of insertion order."""
        t1 = make_scheduled(make_task("t1"), 12, 0, 12, 15)   # noon
        t2 = make_scheduled(make_task("t2"),  7, 0,  7, 15)   # 7 AM — inserted second
        plan = self._plan_with_tasks([t1, t2])
        lines = plan.display_summary().splitlines()
        task_lines = [l for l in lines if "07:00" in l or "12:00" in l]
        assert "07:00" in task_lines[0]
        assert "12:00" in task_lines[1]

    def test_scheduler_prioritizes_higher_priority_first(self):
        """Scheduler._prioritize() must rank P5 before P3 tasks."""
        scheduler = Scheduler()
        tasks = [make_task("low", priority=3), make_task("high", priority=5)]
        ranked = scheduler._prioritize(tasks)
        assert ranked[0].task_id == "high"
        assert ranked[1].task_id == "low"

    def test_scheduler_tiebreaks_by_time_of_day(self):
        """Equal-priority tasks must be ordered morning before evening."""
        scheduler = Scheduler()
        tasks = [
            make_task("eve",  priority=4, preferred_time=TimeOfDay.EVENING),
            make_task("morn", priority=4, preferred_time=TimeOfDay.MORNING),
        ]
        ranked = scheduler._prioritize(tasks)
        assert ranked[0].task_id == "morn"
        assert ranked[1].task_id == "eve"

    def test_assigned_times_are_back_to_back_in_same_band(self):
        """Two tasks in the same band must be scheduled consecutively with no gap."""
        scheduler = Scheduler()
        t1 = make_task("t1", duration=20, preferred_time=TimeOfDay.MORNING)
        t2 = make_task("t2", duration=10, preferred_time=TimeOfDay.MORNING)
        scheduled = scheduler._assign_times([t1, t2], date.today())
        assert scheduled[0].end_time == scheduled[1].start_time


# ---------------------------------------------------------------------------
# Conflict Detection Tests
# ---------------------------------------------------------------------------

class TestConflictDetection:
    def test_no_conflict_when_tasks_back_to_back(self):
        """Tasks ending exactly when the next begins must NOT trigger a conflict."""
        t1 = make_scheduled(make_task("t1"), 7, 0, 7, 30)
        t2 = make_scheduled(make_task("t2"), 7, 30, 8, 0)
        scheduler = Scheduler()
        warnings = scheduler._detect_overlaps([t1, t2])
        assert warnings == []

    def test_conflict_when_tasks_overlap(self):
        """Two overlapping tasks must produce exactly one warning."""
        t1 = make_scheduled(make_task("t1"), 7,  0, 7, 30)
        t2 = make_scheduled(make_task("t2"), 7, 15, 7, 45)
        scheduler = Scheduler()
        warnings = scheduler._detect_overlaps([t1, t2])
        assert len(warnings) == 1

    def test_conflict_fully_contained_task(self):
        """A task fully inside another's window must be flagged as a conflict."""
        outer = make_scheduled(make_task("outer"), 7, 0, 9, 0)
        inner = make_scheduled(make_task("inner"), 7, 30, 8, 0)
        scheduler = Scheduler()
        warnings = scheduler._detect_overlaps([outer, inner])
        assert len(warnings) == 1

    def test_no_conflict_single_task(self):
        """A plan with one task must produce no conflict warnings."""
        t1 = make_scheduled(make_task("t1"), 7, 0, 7, 30)
        scheduler = Scheduler()
        assert scheduler._detect_overlaps([t1]) == []

    def test_cross_pet_conflict_detected(self):
        """Tasks for two different pets at the same time must produce a cross-pet warning."""
        owner = make_owner()
        pet_a = Pet(name="Buddy", species="Dog", breed="Lab", age_years=3, weight_lbs=60.0)
        pet_b = Pet(name="Luna",  species="Cat", breed="Siamese", age_years=5, weight_lbs=9.0)
        owner.add_pet(pet_a)
        owner.add_pet(pet_b)

        plan_a = DailyPlan(date.today(), pet_a, owner, scheduled_tasks=[
            make_scheduled(make_task("a1"), 7, 0, 7, 30),
        ])
        plan_b = DailyPlan(date.today(), pet_b, owner, scheduled_tasks=[
            make_scheduled(make_task("b1"), 7, 0, 7, 20),
        ])
        scheduler = Scheduler()
        warnings = scheduler._detect_cross_pet_overlaps([plan_a, plan_b])
        assert len(warnings) == 1
        assert "Cross-pet" in warnings[0]

    def test_cross_pet_no_conflict_when_sequential(self):
        """Non-overlapping tasks across pets must not produce cross-pet warnings."""
        owner = make_owner()
        pet_a = Pet(name="Buddy", species="Dog", breed="Lab", age_years=3, weight_lbs=60.0)
        pet_b = Pet(name="Luna",  species="Cat", breed="Siamese", age_years=5, weight_lbs=9.0)
        owner.add_pet(pet_a)
        owner.add_pet(pet_b)

        plan_a = DailyPlan(date.today(), pet_a, owner, scheduled_tasks=[
            make_scheduled(make_task("a1"), 7, 0, 7, 30),
        ])
        plan_b = DailyPlan(date.today(), pet_b, owner, scheduled_tasks=[
            make_scheduled(make_task("b1"), 7, 30, 8, 0),
        ])
        scheduler = Scheduler()
        warnings = scheduler._detect_cross_pet_overlaps([plan_a, plan_b])
        assert warnings == []

    def test_intervals_overlap_helper_same_start(self):
        """Two intervals starting at the same time must overlap."""
        assert _intervals_overlap(time(7, 0), time(7, 30), time(7, 0), time(7, 20)) is True

    def test_intervals_overlap_helper_adjacent_no_overlap(self):
        """Adjacent intervals sharing only an endpoint must not overlap."""
        assert _intervals_overlap(time(7, 0), time(7, 30), time(7, 30), time(8, 0)) is False


# ---------------------------------------------------------------------------
# Budget Fitting Tests
# ---------------------------------------------------------------------------

class TestBudgetFitting:
    def test_task_exactly_fitting_budget_is_included(self):
        """A task whose duration equals the budget exactly must be selected."""
        scheduler = Scheduler()
        tasks = [make_task("t1", duration=60)]
        selected = scheduler._select_within_budget(tasks, budget_minutes=60)
        assert len(selected) == 1

    def test_task_exceeding_budget_by_one_minute_is_excluded(self):
        """A task one minute over budget must not be selected."""
        scheduler = Scheduler()
        tasks = [make_task("t1", duration=61)]
        selected = scheduler._select_within_budget(tasks, budget_minutes=60)
        assert selected == []

    def test_empty_task_list_returns_empty(self):
        """Passing an empty task list must return an empty selection."""
        scheduler = Scheduler()
        assert scheduler._select_within_budget([], budget_minutes=60) == []

    def test_greedy_stops_after_budget_exhausted(self):
        """Once the budget is used up, remaining tasks must be skipped."""
        scheduler = Scheduler()
        tasks = [
            make_task("big",   duration=55, priority=5),
            make_task("small", duration=10, priority=3),
        ]
        selected = scheduler._select_within_budget(tasks, budget_minutes=60)
        assert len(selected) == 1
        assert selected[0].task_id == "big"

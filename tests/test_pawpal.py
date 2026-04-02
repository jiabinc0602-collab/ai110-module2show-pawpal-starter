from pawpal_system import Pet, Task, TaskCategory


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_task(task_id="t1", priority=3):
    """Return a minimal Task instance for use in tests."""
    return Task(
        task_id=task_id,
        name="Test Task",
        category=TaskCategory.OTHER,
        duration_minutes=15,
        priority=priority,
    )


def make_pet():
    """Return a minimal Pet instance for use in tests."""
    return Pet(name="Buddy", species="Dog", breed="Labrador", age_years=3, weight_lbs=60.0)


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

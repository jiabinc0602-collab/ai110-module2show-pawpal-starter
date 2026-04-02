from pawpal_system import (
    Owner, Pet,
    Task, WalkTask,
    TaskCategory, TimeOfDay, RecurrenceRule,
    Scheduler,
)

# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------
owner = Owner(
    name="Alex Rivera",
    email="alex@example.com",
    time_available_minutes=90,
)

# ---------------------------------------------------------------------------
# Pets
# ---------------------------------------------------------------------------
buddy = Pet(name="Buddy", species="Dog", breed="Labrador", age_years=3, weight_lbs=65.0)
luna  = Pet(name="Luna",  species="Cat", breed="Siamese",  age_years=5, weight_lbs=9.5)

owner.add_pet(buddy)
owner.add_pet(luna)

# ---------------------------------------------------------------------------
# Buddy's tasks
# ---------------------------------------------------------------------------
buddy.add_task(WalkTask(
    task_id="b1", name="Morning Walk", category=TaskCategory.WALK,
    duration_minutes=30, priority=5, preferred_time=TimeOfDay.MORNING,
    pet=buddy, recurrence=RecurrenceRule.DAILY,
    distance_miles=1.2, route_notes="Oak Street loop",
))
buddy.add_task(Task(
    task_id="b2", name="Afternoon Feeding", category=TaskCategory.FEEDING,
    duration_minutes=10, priority=4, preferred_time=TimeOfDay.AFTERNOON,
    notes="Half cup dry kibble", pet=buddy, recurrence=RecurrenceRule.DAILY,
))
buddy.add_task(Task(
    task_id="b3", name="Grooming Brush", category=TaskCategory.GROOMING,
    duration_minutes=15, priority=2, preferred_time=TimeOfDay.EVENING,
    pet=buddy, recurrence=RecurrenceRule.WEEKDAYS,
))

# ---------------------------------------------------------------------------
# Luna's tasks — Morning Vet Checkup intentionally overlaps Buddy's Morning Walk
# ---------------------------------------------------------------------------
luna.add_task(Task(
    task_id="l1", name="Morning Vet Checkup", category=TaskCategory.OTHER,
    duration_minutes=20, priority=5, preferred_time=TimeOfDay.MORNING,
    notes="Annual exam — starts at 7:00 AM, same slot as Buddy's walk",
    pet=luna, recurrence=RecurrenceRule.NONE,
))
luna.add_task(Task(
    task_id="l2", name="Morning Feeding", category=TaskCategory.FEEDING,
    duration_minutes=5, priority=5, preferred_time=TimeOfDay.MORNING,
    pet=luna, recurrence=RecurrenceRule.DAILY,
))
luna.add_task(Task(
    task_id="l3", name="Evening Enrichment", category=TaskCategory.ENRICHMENT,
    duration_minutes=20, priority=3, preferred_time=TimeOfDay.EVENING,
    notes="Puzzle feeder", pet=luna, recurrence=RecurrenceRule.DAILY,
))

# ---------------------------------------------------------------------------
# Demo 1: auto-next-occurrence
# ---------------------------------------------------------------------------
print("=" * 52)
print("  DEMO 1 — Auto next-occurrence on complete")
print("=" * 52)
print(f"Buddy tasks before: {[t.task_id for t in buddy.tasks]}")

buddy.complete_task("b2")   # complete Afternoon Feeding (DAILY)

print(f"Buddy tasks after : {[t.task_id for t in buddy.tasks]}")
completed = next(t for t in buddy.tasks if t.task_id == "b2")
next_occ  = next(t for t in buddy.tasks if t.task_id != "b2" and "b2" in t.task_id)
print(f"  '{completed.name}' is_complete={completed.is_complete}")
print(f"  Next occurrence  : task_id='{next_occ.task_id}'  due={next_occ.due_date}")
print()

# ---------------------------------------------------------------------------
# Demo 2: full schedule with conflict detection
# ---------------------------------------------------------------------------
print("=" * 52)
print("  DEMO 2 — Full schedule + conflict detection")
print("=" * 52)

scheduler = Scheduler()
plans = scheduler.generate_all_plans(owner)

for plan in plans:
    print()
    print(plan.display_summary())
    print()
    print("  Reasoning:")
    for line in plan.reasoning.splitlines():
        print(f"    {line}")
    print()

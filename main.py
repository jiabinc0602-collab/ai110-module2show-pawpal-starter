from datetime import date, time

from pawpal_system import (
    Owner, Pet,
    Task, WalkTask,
    TaskCategory, TimeOfDay,
    ScheduledTask, DailyPlan,
)

# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------
owner = Owner(
    name="Alex Rivera",
    email="alex@example.com",
    time_available_minutes=120,
    preferences="Prefers morning walks before work",
)

# ---------------------------------------------------------------------------
# Pets
# ---------------------------------------------------------------------------
buddy = Pet(name="Buddy", species="Dog", breed="Labrador", age_years=3, weight_lbs=65.0)
luna  = Pet(name="Luna",  species="Cat", breed="Siamese",  age_years=5, weight_lbs=9.5)

owner.pets.extend([buddy, luna])

# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------
morning_walk = WalkTask(
    task_id="t1",
    name="Morning Walk",
    category=TaskCategory.WALK,
    duration_minutes=30,
    priority=5,
    preferred_time=TimeOfDay.MORNING,
    notes="Around the park",
    distance_miles=1.2,
    route_notes="Oak Street loop",
    pet=buddy,
)

afternoon_feeding = Task(
    task_id="t2",
    name="Afternoon Feeding",
    category=TaskCategory.FEEDING,
    duration_minutes=10,
    priority=4,
    preferred_time=TimeOfDay.AFTERNOON,
    notes="Half cup dry kibble",
    pet=buddy,
)

evening_enrichment = Task(
    task_id="t3",
    name="Evening Enrichment",
    category=TaskCategory.ENRICHMENT,
    duration_minutes=20,
    priority=3,
    preferred_time=TimeOfDay.EVENING,
    notes="Puzzle feeder for Luna",
    pet=luna,
)

buddy.tasks.extend([morning_walk, afternoon_feeding])
luna.tasks.append(evening_enrichment)

# ---------------------------------------------------------------------------
# Build a simple daily plan (manual schedule — Scheduler logic pending)
# ---------------------------------------------------------------------------
plan = DailyPlan(
    plan_date=date.today(),
    pet=buddy,
    owner=owner,
    scheduled_tasks=[
        ScheduledTask(task=morning_walk,      start_time=time(7, 0),  end_time=time(7, 30)),
        ScheduledTask(task=afternoon_feeding, start_time=time(12, 0), end_time=time(12, 10)),
        ScheduledTask(task=evening_enrichment,start_time=time(18, 0), end_time=time(18, 20)),
    ],
    reasoning="High-priority tasks scheduled first; Luna's enrichment slotted in the evening slot.",
)

# ---------------------------------------------------------------------------
# Print Today's Schedule
# ---------------------------------------------------------------------------
print("=" * 44)
print("         PAWPAL+  —  TODAY'S SCHEDULE")
print("=" * 44)
print(f"Owner : {owner.name}")
print(f"Date  : {plan.plan_date.strftime('%A, %B %d %Y')}")
print(f"Budget: {owner.time_available_minutes} min available")
print("-" * 44)

for st in plan.scheduled_tasks:
    start = st.start_time.strftime("%I:%M %p")
    end   = st.end_time.strftime("%I:%M %p")
    pet_name = st.task.pet.name if st.task.pet else "?"
    print(f"  {start} – {end}  [{st.task.category.value.upper():11}]  "
          f"{st.task.name} ({pet_name}, {st.task.duration_minutes} min, P{st.task.priority})")

print("-" * 44)
total = sum(st.task.duration_minutes for st in plan.scheduled_tasks)
print(f"  Total scheduled: {total} min")
print()
print(f"  Reasoning: {plan.reasoning}")
print("=" * 44)

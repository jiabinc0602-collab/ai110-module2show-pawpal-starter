import streamlit as st
from pawpal_system import Owner, Pet, Task, TaskCategory, TimeOfDay, RecurrenceRule, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
if "owner" not in st.session_state:
    st.session_state.owner = None
if "plans" not in st.session_state:
    st.session_state.plans = []

# ---------------------------------------------------------------------------
# Owner setup
# ---------------------------------------------------------------------------
st.subheader("Owner Info")

with st.form("owner_form"):
    owner_name     = st.text_input("Your name", value="Jordan")
    owner_email    = st.text_input("Email", value="jordan@example.com")
    time_available = st.number_input("Time available today (min)", min_value=10, max_value=480, value=120)
    save_owner     = st.form_submit_button("Save Owner")

if save_owner:
    st.session_state.owner = Owner(
        name=owner_name,
        email=owner_email,
        time_available_minutes=int(time_available),
    )
    st.session_state.plans = []     # reset plans when owner changes

if st.session_state.owner is None:
    st.info("Fill in owner info above to get started.")
    st.stop()

owner: Owner = st.session_state.owner
st.success(f"Owner: **{owner.name}** | Budget: {owner.time_available_minutes} min")

st.divider()

# ---------------------------------------------------------------------------
# Add a Pet
# ---------------------------------------------------------------------------
st.subheader("Add a Pet")

with st.form("pet_form"):
    col1, col2 = st.columns(2)
    with col1:
        pet_name = st.text_input("Pet name", value="Mochi")
        species  = st.selectbox("Species", ["dog", "cat", "other"])
    with col2:
        breed  = st.text_input("Breed", value="Mixed")
        age    = st.number_input("Age (years)", min_value=0, max_value=30, value=2)
        weight = st.number_input("Weight (lbs)", min_value=0.1, max_value=300.0, value=15.0)
    add_pet = st.form_submit_button("Add Pet")

if add_pet:
    owner.add_pet(Pet(
        name=pet_name, species=species, breed=breed,
        age_years=int(age), weight_lbs=float(weight),
    ))
    st.success(f"Added {pet_name}!")

if not owner.get_pets():
    st.info("No pets yet. Add one above.")
    st.stop()

st.divider()

# ---------------------------------------------------------------------------
# Schedule a Task
# ---------------------------------------------------------------------------
st.subheader("Schedule a Task")

CATEGORY_MAP   = {c.value: c for c in TaskCategory}
PRIORITY_MAP   = {"Low (1)": 1, "Medium (2)": 2, "Normal (3)": 3, "High (4)": 4, "Critical (5)": 5}
TIME_MAP       = {t.value: t for t in TimeOfDay}
RECURRENCE_MAP = {r.value: r for r in RecurrenceRule}

pets          = owner.get_pets()
pet_names     = [p.name for p in pets]
selected_name = st.selectbox("Select pet", pet_names)
selected_pet  = next(p for p in pets if p.name == selected_name)

with st.form("task_form"):
    col1, col2, col3 = st.columns(3)
    with col1:
        task_name    = st.text_input("Task name", value="Morning Walk")
        category_key = st.selectbox("Category", list(CATEGORY_MAP.keys()))
    with col2:
        duration     = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
        priority_key = st.selectbox("Priority", list(PRIORITY_MAP.keys()), index=2)
    with col3:
        time_keys     = list(TIME_MAP.keys())
        time_key      = st.selectbox("Time of day", time_keys, index=time_keys.index("any"))
        recurrence_key = st.selectbox("Recurrence", list(RECURRENCE_MAP.keys()))
    notes    = st.text_input("Notes", value="")
    add_task = st.form_submit_button("Add Task")

if add_task:
    task_id = f"{selected_pet.name}_{len(selected_pet.tasks) + 1}"
    selected_pet.add_task(Task(
        task_id=task_id,
        name=task_name,
        category=CATEGORY_MAP[category_key],
        duration_minutes=int(duration),
        priority=PRIORITY_MAP[priority_key],
        preferred_time=TIME_MAP[time_key],
        recurrence=RECURRENCE_MAP[recurrence_key],
        notes=notes,
        pet=selected_pet,
    ))
    st.success(f"Added '{task_name}' to {selected_pet.name}!")

# Quick overview of current tasks per pet
st.subheader("Current Tasks")
for pet in owner.get_pets():
    with st.expander(f"{pet.name} — {len(pet.tasks)} task(s)"):
        if pet.tasks:
            st.table([
                {
                    "Task": t.name,
                    "Category": t.category.value,
                    "Duration (min)": t.duration_minutes,
                    "Priority": t.priority,
                    "Time of Day": t.preferred_time.value,
                    "Recurrence": t.recurrence.value,
                }
                for t in pet.tasks
            ])
        else:
            st.caption("No tasks yet.")

st.divider()

# ---------------------------------------------------------------------------
# Generate Schedule  →  Scheduler.generate_all_plans()
# ---------------------------------------------------------------------------
st.subheader("Generate Schedule")

if st.button("Generate schedule", type="primary"):
    st.session_state.plans = Scheduler().generate_all_plans(owner)

if not st.session_state.plans:
    st.caption("Add tasks above, then click Generate schedule.")
    st.stop()

# ---------------------------------------------------------------------------
# Display each pet's plan
# ---------------------------------------------------------------------------
for plan in st.session_state.plans:
    st.markdown(f"### {plan.pet.name}")

    # Budget metric
    remaining = plan.owner.time_available_minutes - plan.total_duration_minutes
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Scheduled", f"{plan.total_duration_minutes} min")
    col_b.metric("Budget", f"{plan.owner.time_available_minutes} min")
    col_c.metric("Remaining", f"{remaining} min", delta=f"{remaining} min",
                 delta_color="normal" if remaining >= 0 else "inverse")

    # Conflict warnings
    if plan.warnings:
        for w in plan.warnings:
            st.warning(w)
    else:
        st.success("No scheduling conflicts.")

    # Tabs: full plan / walks / remaining
    tab_all, tab_walks, tab_remaining, tab_reasoning = st.tabs(
        ["Full Plan", "Walks", "Remaining Tasks", "Reasoning"]
    )

    def _rows(scheduled_tasks):
        return [
            {
                "Time": f"{s.start_time.strftime('%I:%M %p')} – {s.end_time.strftime('%I:%M %p')}",
                "Task": s.task.name,
                "Category": s.task.category.value,
                "Priority": s.task.priority,
                "Recurrence": s.task.recurrence.value,
                "Done": "Yes" if s.task.is_complete else "No",
            }
            for s in sorted(scheduled_tasks, key=lambda x: x.start_time)
        ]

    with tab_all:
        rows = _rows(plan.scheduled_tasks)
        if rows:
            st.table(rows)
        else:
            st.info("No tasks were scheduled. Check task durations against your budget.")

    with tab_walks:
        walks = plan.get_walks()
        if walks:
            st.table(_rows(walks))
        else:
            st.info("No walks scheduled for this pet today.")

    with tab_remaining:
        incomplete = plan.get_incomplete()
        if incomplete:
            st.table(_rows(incomplete))
        else:
            st.success("All tasks for this pet are complete!")

    with tab_reasoning:
        st.code(plan.reasoning, language=None)

    st.divider()

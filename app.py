import streamlit as st
from pawpal_system import Owner, Pet, Task, TaskCategory, TimeOfDay

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# ---------------------------------------------------------------------------
# Session state — check before creating so reruns don't reset data
# ---------------------------------------------------------------------------
if "owner" not in st.session_state:
    st.session_state.owner = None

# ---------------------------------------------------------------------------
# Owner setup
# ---------------------------------------------------------------------------
st.subheader("Owner Info")

with st.form("owner_form"):
    owner_name      = st.text_input("Your name", value="Jordan")
    owner_email     = st.text_input("Email", value="jordan@example.com")
    time_available  = st.number_input("Time available today (min)", min_value=10, max_value=480, value=120)
    save_owner      = st.form_submit_button("Save Owner")

if save_owner:
    st.session_state.owner = Owner(
        name=owner_name,
        email=owner_email,
        time_available_minutes=int(time_available),
    )

if st.session_state.owner is None:
    st.info("Fill in owner info above to get started.")
    st.stop()

owner: Owner = st.session_state.owner
st.success(f"Owner: **{owner.name}** | Budget: {owner.time_available_minutes} min")

st.divider()

# ---------------------------------------------------------------------------
# Add a Pet  →  calls Owner.add_pet()
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
    new_pet = Pet(
        name=pet_name,
        species=species,
        breed=breed,
        age_years=int(age),
        weight_lbs=float(weight),
    )
    owner.add_pet(new_pet)
    st.success(f"Added {pet_name}!")

if not owner.get_pets():
    st.info("No pets yet. Add one above.")
    st.stop()

st.divider()

# ---------------------------------------------------------------------------
# Schedule a Task  →  calls Pet.add_task()
# ---------------------------------------------------------------------------
st.subheader("Schedule a Task")

CATEGORY_MAP = {c.value: c for c in TaskCategory}
PRIORITY_MAP  = {"Low (1)": 1, "Medium (2)": 2, "Normal (3)": 3, "High (4)": 4, "Critical (5)": 5}
TIME_MAP      = {t.value: t for t in TimeOfDay}

pets          = owner.get_pets()                       # Fix 6: single call, reused below
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
        time_keys = list(TIME_MAP.keys())               # Fix 6: build once, index into same list
        time_key  = st.selectbox("Time of day", time_keys, index=time_keys.index("any"))
        notes    = st.text_input("Notes", value="")
    add_task = st.form_submit_button("Add Task")

if add_task:
    task_id  = f"{selected_pet.name}_{len(selected_pet.tasks) + 1}"
    new_task = Task(
        task_id=task_id,
        name=task_name,
        category=CATEGORY_MAP[category_key],
        duration_minutes=int(duration),
        priority=PRIORITY_MAP[priority_key],
        preferred_time=TIME_MAP[time_key],
        notes=notes,
        pet=selected_pet,
    )
    selected_pet.add_task(new_task)
    st.success(f"Added '{task_name}' to {selected_pet.name}!")

st.divider()

# ---------------------------------------------------------------------------
# Today's plan view
# ---------------------------------------------------------------------------
st.subheader("Today's Pets & Tasks")

for pet in owner.get_pets():
    st.markdown(f"**{pet.name}** — {pet.species}, {pet.breed}, {pet.age_years} yr, {pet.weight_lbs} lbs")
    if pet.tasks:
        st.table([
            {
                "Task": t.name,
                "Category": t.category.value,
                "Duration (min)": t.duration_minutes,
                "Priority": t.priority,
                "Time of Day": t.preferred_time.value,
                "Notes": t.notes,
            }
            for t in pet.tasks
        ])
    else:
        st.caption("No tasks yet.")

st.divider()

# ---------------------------------------------------------------------------
# Generate schedule (pending Scheduler implementation)
# ---------------------------------------------------------------------------
st.subheader("Generate Schedule")
st.caption("Calls Scheduler.generate_plan() once the logic is implemented.")

if st.button("Generate schedule"):
    st.warning("Scheduler not yet implemented — add logic to Scheduler.generate_plan() in pawpal_system.py.")

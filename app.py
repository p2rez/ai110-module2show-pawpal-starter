import streamlit as st
from pawpal_system import Task, Pet, Owner, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")
st.caption("A pet care planning assistant for busy pet owners.")

st.divider()

# --- Owner Setup ---
st.subheader("Owner")
owner_name = st.text_input("Owner name", value="Jordan")
available_minutes = st.number_input("Available time today (minutes)", min_value=1, max_value=480, value=60)

if "owner" not in st.session_state:
    st.session_state.owner = Owner(name=owner_name, available_minutes=available_minutes)

# --- Add a Pet ---
st.subheader("Add a Pet")
col1, col2, col3 = st.columns(3)
with col1:
    pet_name = st.text_input("Pet name", value="Mochi")
with col2:
    species = st.selectbox("Species", ["dog", "cat", "other"])
with col3:
    age = st.number_input("Age", min_value=0, max_value=30, value=2)

if st.button("Add pet"):
    new_pet = Pet(name=pet_name, species=species, age=age)
    st.session_state.owner.add_pet(new_pet)
    st.success(f"Added {pet_name} the {species}!")

# Show registered pets
pets = st.session_state.owner.pets
if pets:
    st.write("Registered pets:")
    st.table([{"Name": p.name, "Species": p.species, "Age": p.age, "Tasks": len(p.get_tasks())} for p in pets])
else:
    st.info("No pets added yet.")

st.divider()

# --- Add a Task ---
st.subheader("Add a Task")
if not pets:
    st.warning("Add a pet first before adding tasks.")
else:
    pet_names = [p.name for p in pets]
    selected_pet_name = st.selectbox("Assign task to", pet_names)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        task_desc = st.text_input("Task description", value="Morning walk")
    with col2:
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
    with col3:
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
    with col4:
        frequency = st.selectbox("Frequency", ["daily", "weekly", "as needed"])

    if st.button("Add task"):
        selected_pet = next(p for p in pets if p.name == selected_pet_name)
        selected_pet.add_task(Task(
            description=task_desc,
            duration=int(duration),
            priority=priority,
            frequency=frequency
        ))
        st.success(f"Added '{task_desc}' to {selected_pet_name}.")

    # Show all current tasks across pets with filter and sort controls
    all_tasks = st.session_state.owner.get_all_tasks()
    if all_tasks:
        st.write("Current tasks:")
        fcol1, fcol2, fcol3 = st.columns(3)
        with fcol1:
            filter_pet = st.selectbox("Filter by pet", ["All"] + [p.name for p in pets], key="filter_pet")
        with fcol2:
            filter_status = st.selectbox("Filter by status", ["All", "Pending", "Done"], key="filter_status")
        with fcol3:
            sort_by_duration = st.selectbox("Sort duration", ["Default", "Shortest first", "Longest first"], key="sort_dur")

        def pet_of(task):
            return next((p.name for p in pets if task in p.get_tasks()), "?")

        displayed = all_tasks
        if filter_pet != "All":
            displayed = [t for t in displayed if pet_of(t) == filter_pet]
        if filter_status == "Pending":
            displayed = [t for t in displayed if not t.completed]
        elif filter_status == "Done":
            displayed = [t for t in displayed if t.completed]
        if sort_by_duration == "Shortest first":
            displayed = sorted(displayed, key=lambda t: t.duration)
        elif sort_by_duration == "Longest first":
            displayed = sorted(displayed, key=lambda t: t.duration, reverse=True)

        if displayed:
            st.table([{
                "Pet": pet_of(t),
                "Task": t.description,
                "Duration (min)": t.duration,
                "Priority": t.priority,
                "Frequency": t.frequency,
                "Done": t.completed
            } for t in displayed])
        else:
            st.info("No tasks match the selected filters.")
    else:
        st.info("No tasks yet. Add one above.")

st.divider()

# --- Generate Schedule ---
st.subheader("Build Schedule")

if st.button("Generate schedule"):
    all_tasks = st.session_state.owner.get_all_tasks()
    if not all_tasks:
        st.warning("Add at least one task before generating a schedule.")
    else:
        scheduler = Scheduler(st.session_state.owner)
        scheduler.build_schedule()

        # Conflict detection — show warnings before results
        conflicts = scheduler.detect_conflicts()
        if conflicts:
            st.subheader("Conflicts & Warnings")
            for issue in conflicts:
                st.warning(issue)

        st.success("Schedule generated!")
        st.text(scheduler.explain())

        # Recurring task weekly view
        recurring = scheduler.get_recurring_summary()
        has_recurring = any(recurring[day] for day in recurring)
        if has_recurring:
            st.subheader("Recurring Task Overview (this week)")
            days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            weekly_rows = []
            for day in days:
                for task in recurring[day]:
                    weekly_rows.append({
                        "Day": day,
                        "Task": task.description,
                        "Duration (min)": task.duration,
                        "Frequency": task.frequency,
                        "Priority": task.priority,
                    })
            if weekly_rows:
                st.table(weekly_rows)

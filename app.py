import streamlit as st
from pawpal_system import Task, Pet, Owner, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")
st.caption("A pet care planning assistant for busy pet owners.")

st.divider()

# ── Owner Setup ───────────────────────────────────────────────────────────────
st.subheader("Owner")
owner_name = st.text_input("Owner name", value="Jordan")
available_minutes = st.number_input(
    "Available time today (minutes)", min_value=1, max_value=480, value=60
)

if "owner" not in st.session_state:
    st.session_state.owner = Owner(name=owner_name, available_minutes=available_minutes)

# ── Add a Pet ─────────────────────────────────────────────────────────────────
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

pets = st.session_state.owner.pets
if pets:
    st.table([
        {"Name": p.name, "Species": p.species, "Age": p.age, "Tasks": len(p.get_tasks())}
        for p in pets
    ])
else:
    st.info("No pets added yet.")

st.divider()

# ── Add a Task ────────────────────────────────────────────────────────────────
st.subheader("Add a Task")
if not pets:
    st.warning("Add a pet first before adding tasks.")
else:
    pet_names = [p.name for p in pets]
    selected_pet_name = st.selectbox("Assign task to", pet_names)

    col1, col2, col3 = st.columns(3)
    with col1:
        task_desc = st.text_input("Task description", value="Morning walk")
    with col2:
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
    with col3:
        task_time = st.text_input("Start time (HH:MM)", value="08:00")

    col4, col5 = st.columns(2)
    with col4:
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
    with col5:
        frequency = st.selectbox("Frequency", ["daily", "weekly", "as needed"])

    if st.button("Add task"):
        try:
            selected_pet = next(p for p in pets if p.name == selected_pet_name)
            selected_pet.add_task(Task(
                description=task_desc,
                duration=int(duration),
                priority=priority,
                frequency=frequency,
                time=task_time,
            ))
            st.success(f"Added '{task_desc}' to {selected_pet_name} at {task_time}.")
        except ValueError as e:
            st.error(f"Could not add task: {e}")

    # ── Task table with filter + sort controls ────────────────────────────────
    all_tasks = st.session_state.owner.get_all_tasks()
    if all_tasks:
        st.markdown("**Current tasks**")

        def pet_of(task):
            return next((p.name for p in pets if task in p.get_tasks()), "?")

        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            filter_pet = st.selectbox(
                "Filter by pet", ["All"] + [p.name for p in pets], key="filter_pet"
            )
        with fc2:
            filter_status = st.selectbox(
                "Filter by status", ["All", "Pending", "Done"], key="filter_status"
            )
        with fc3:
            sort_choice = st.selectbox(
                "Sort by",
                ["Start time (earliest first)", "Start time (latest first)",
                 "Duration (shortest first)", "Duration (longest first)"],
                key="sort_choice",
            )

        displayed = all_tasks
        if filter_pet != "All":
            displayed = [t for t in displayed if pet_of(t) == filter_pet]
        if filter_status == "Pending":
            displayed = [t for t in displayed if not t.completed]
        elif filter_status == "Done":
            displayed = [t for t in displayed if t.completed]

        if sort_choice == "Start time (earliest first)":
            displayed = sorted(
                displayed, key=lambda t: tuple(int(p) for p in t.time.split(":"))
            )
        elif sort_choice == "Start time (latest first)":
            displayed = sorted(
                displayed, key=lambda t: tuple(int(p) for p in t.time.split(":")), reverse=True
            )
        elif sort_choice == "Duration (shortest first)":
            displayed = sorted(displayed, key=lambda t: t.duration)
        elif sort_choice == "Duration (longest first)":
            displayed = sorted(displayed, key=lambda t: t.duration, reverse=True)

        if displayed:
            st.dataframe(
                [{
                    "Pet": pet_of(t),
                    "Task": t.description,
                    "Start": t.time,
                    "Duration (min)": t.duration,
                    "Priority": t.priority,
                    "Frequency": t.frequency,
                    "Done": "✓" if t.completed else "○",
                } for t in displayed],
                use_container_width=True,
            )
        else:
            st.info("No tasks match the selected filters.")
    else:
        st.info("No tasks yet. Add one above.")

st.divider()

# ── Build Schedule ────────────────────────────────────────────────────────────
st.subheader("Build Schedule")

if st.button("Generate schedule"):
    all_tasks = st.session_state.owner.get_all_tasks()
    if not all_tasks:
        st.warning("Add at least one task before generating a schedule.")
    else:
        scheduler = Scheduler(st.session_state.owner)
        scheduler.build_schedule()
        st.session_state.scheduler = scheduler   # persist so results survive reruns

# Render schedule results from session state so they survive Streamlit reruns
if "scheduler" in st.session_state:
    scheduler = st.session_state.scheduler

    # ── Time budget summary ───────────────────────────────────────────────────
    total = scheduler.total_time_scheduled()
    budget = st.session_state.owner.available_minutes
    skipped_count = len(scheduler.skipped)

    st.markdown("#### Time Budget")
    m1, m2, m3 = st.columns(3)
    m1.metric("Scheduled", f"{total} min")
    m2.metric("Budget", f"{budget} min")
    m3.metric("Tasks skipped", skipped_count, delta=f"-{skipped_count}" if skipped_count else None,
              delta_color="inverse")

    progress_pct = min(total / budget, 1.0) if budget > 0 else 0
    st.progress(progress_pct, text=f"{total} / {budget} min used")

    # ── Conflict warnings — grouped by type ──────────────────────────────────
    conflicts = scheduler.detect_conflicts()
    if conflicts:
        st.markdown("#### ⚠️ Conflicts Detected")
        st.caption(
            "Fix these before relying on your schedule. Each warning tells you "
            "exactly which task or pet is involved."
        )

        time_conflicts   = [m for m in conflicts if "Time conflict" in m]
        overload_msgs    = [m for m in conflicts if "overload" in m.lower()]
        never_fit_msgs   = [m for m in conflicts if "can never be scheduled" in m]
        duplicate_msgs   = [m for m in conflicts if "Duplicate" in m]

        if time_conflicts:
            st.error("**Same-time clashes** — two tasks are scheduled at the same moment:")
            for msg in time_conflicts:
                # Parse the message to build a small detail table
                # Format: "Time conflict at HH:MM: 'A' (Pet1), 'B' (Pet2) are all..."
                st.markdown(f"- {msg}")
            st.caption(
                "Tip: open the task list above, filter by the clashing time, "
                "and change one task's start time."
            )

        if overload_msgs:
            for msg in overload_msgs:
                st.warning(f"**Budget overload** — {msg}")
            st.caption(
                "Tip: reduce task durations, lower the priority of non-essential "
                "tasks so they get skipped, or increase your available time."
            )

        if never_fit_msgs:
            for msg in never_fit_msgs:
                st.warning(f"**Task too long** — {msg}")

        if duplicate_msgs:
            for msg in duplicate_msgs:
                st.warning(f"**Duplicate task** — {msg}")
    else:
        st.success("No conflicts detected — your schedule looks clean!")

    # ── Scheduled tasks (sorted by start time) ───────────────────────────────
    scheduled = scheduler.sort_by_time(ascending=True)
    if scheduled:
        st.markdown("#### Today's Schedule")

        def pet_label(task):
            for pet in st.session_state.owner.pets:
                if task in pet.get_tasks():
                    return pet.name
            return "?"

        PRIORITY_EMOJI = {"high": "🔴", "medium": "🟡", "low": "🟢"}

        st.dataframe(
            [{
                "Start": t.time,
                "Task": t.description,
                "Pet": pet_label(t),
                "Duration (min)": t.duration,
                "Priority": f"{PRIORITY_EMOJI.get(t.priority, '')} {t.priority}",
                "Frequency": t.frequency,
                "Done": "✓" if t.completed else "○",
            } for t in scheduled],
            use_container_width=True,
        )
    else:
        st.info("No tasks were scheduled.")

    # ── Skipped tasks ─────────────────────────────────────────────────────────
    if scheduler.skipped:
        with st.expander(f"Skipped tasks ({len(scheduler.skipped)}) — didn't fit the budget"):
            st.dataframe(
                [{
                    "Task": t.description,
                    "Duration (min)": t.duration,
                    "Priority": t.priority,
                    "Frequency": t.frequency,
                } for t in scheduler.skipped],
                use_container_width=True,
            )

    # ── Recurring task overview ───────────────────────────────────────────────
    recurring = scheduler.get_recurring_summary()
    has_recurring = any(recurring[day] for day in recurring)
    if has_recurring:
        st.markdown("#### Recurring Task Overview")
        st.caption("Daily tasks appear every day. Weekly tasks are shown on Monday.")

        # Build a compact table: one row per task showing which days it appears
        seen_tasks: dict[str, set[str]] = {}
        for day, tasks in recurring.items():
            for task in tasks:
                seen_tasks.setdefault(task.description, set()).add(day)

        all_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
                    "Saturday", "Sunday"]
        compact_rows = []
        for desc, days_set in seen_tasks.items():
            # Show day abbreviations in order
            day_str = "  ".join(
                d[:3] for d in all_days if d in days_set
            )
            compact_rows.append({"Task": desc, "Repeats on": day_str})

        st.dataframe(compact_rows, use_container_width=True)

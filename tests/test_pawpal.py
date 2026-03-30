import pytest
from pawpal_system import Task, Pet, Owner, Scheduler


# ── Fixtures ──────────────────────────────────────────────────────────────────

def make_scheduler(available_minutes=60, tasks_by_pet=None):
    """Helper: build an Owner + Scheduler pre-loaded with tasks.

    tasks_by_pet: dict of {pet_name: [Task, ...]}
    """
    owner = Owner(name="Test Owner", available_minutes=available_minutes)
    for pet_name, tasks in (tasks_by_pet or {}).items():
        pet = Pet(name=pet_name, species="dog", age=2)
        for t in tasks:
            pet.add_task(t)
        owner.add_pet(pet)
    scheduler = Scheduler(owner)
    scheduler.build_schedule()
    return scheduler


# ══════════════════════════════════════════════════════════════════════════════
# 1. build_schedule — priority ordering
# ══════════════════════════════════════════════════════════════════════════════

def test_build_schedule_high_priority_scheduled_before_low():
    """High-priority tasks must appear in the schedule when the budget is tight."""
    scheduler = make_scheduler(
        available_minutes=20,
        tasks_by_pet={"Buddy": [
            Task("Low task",  duration=15, frequency="daily", priority="low"),
            Task("High task", duration=15, frequency="daily", priority="high"),
        ]}
    )
    descriptions = [t.description for t in scheduler.scheduled]
    assert "High task" in descriptions
    assert "Low task" not in descriptions   # no room for both; low was skipped


def test_build_schedule_priority_order_high_medium_low():
    """With just enough room for two tasks, high and medium win over low."""
    scheduler = make_scheduler(
        available_minutes=25,
        tasks_by_pet={"Buddy": [
            Task("Low task",    duration=10, frequency="daily", priority="low"),
            Task("Medium task", duration=10, frequency="daily", priority="medium"),
            Task("High task",   duration=10, frequency="daily", priority="high"),
        ]}
    )
    scheduled_descs = [t.description for t in scheduler.scheduled]
    assert "High task" in scheduled_descs
    assert "Medium task" in scheduled_descs
    assert "Low task" not in scheduled_descs


# ══════════════════════════════════════════════════════════════════════════════
# 2. build_schedule — time budget
# ══════════════════════════════════════════════════════════════════════════════

def test_build_schedule_never_exceeds_budget():
    """Total scheduled time must never exceed available_minutes."""
    scheduler = make_scheduler(
        available_minutes=30,
        tasks_by_pet={"Buddy": [
            Task("Walk",  duration=20, frequency="daily",  priority="high"),
            Task("Bath",  duration=20, frequency="weekly", priority="medium"),
            Task("Meds",  duration=5,  frequency="daily",  priority="high"),
        ]}
    )
    assert scheduler.total_time_scheduled() <= 30


def test_build_schedule_exact_budget_fit():
    """A task that exactly fills the remaining budget must be scheduled."""
    scheduler = make_scheduler(
        available_minutes=20,
        tasks_by_pet={"Buddy": [
            Task("Walk", duration=20, frequency="daily", priority="high"),
        ]}
    )
    assert len(scheduler.scheduled) == 1
    assert scheduler.total_time_scheduled() == 20


def test_build_schedule_second_pass_recovers_small_task():
    """A small task skipped in the first pass should be recovered in the second pass."""
    # Budget: 25 min. Tasks sorted: high/daily (20 min) → medium/daily (10 min) → low (5 min).
    # First pass: 20 fits, 10 doesn't (only 5 left), 5 is skipped too.
    # Second pass: 5-min task fits in the remaining 5 min → should be recovered.
    scheduler = make_scheduler(
        available_minutes=25,
        tasks_by_pet={"Buddy": [
            Task("Big task",   duration=20, frequency="daily", priority="high"),
            Task("Medium task",duration=10, frequency="daily", priority="medium"),
            Task("Small task", duration=5,  frequency="daily", priority="low"),
        ]}
    )
    descriptions = [t.description for t in scheduler.scheduled]
    assert "Big task" in descriptions
    assert "Small task" in descriptions     # recovered by second pass
    assert "Medium task" not in descriptions


# ══════════════════════════════════════════════════════════════════════════════
# 3. sort_by_time
# ══════════════════════════════════════════════════════════════════════════════

def test_sort_by_time_ascending_order():
    """Tasks added out of order must come back sorted earliest to latest."""
    scheduler = make_scheduler(
        available_minutes=120,
        tasks_by_pet={"Buddy": [
            Task("Evening", duration=10, frequency="daily", priority="low",  time="18:00"),
            Task("Morning", duration=10, frequency="daily", priority="high", time="07:30"),
            Task("Midday",  duration=10, frequency="daily", priority="medium", time="12:15"),
        ]}
    )
    sorted_tasks = scheduler.sort_by_time(ascending=True)
    times = [t.time for t in sorted_tasks]
    assert times == ["07:30", "12:15", "18:00"]


def test_sort_by_time_descending_order():
    """Descending sort must return latest time first."""
    scheduler = make_scheduler(
        available_minutes=120,
        tasks_by_pet={"Buddy": [
            Task("Morning", duration=10, frequency="daily", priority="high", time="07:30"),
            Task("Evening", duration=10, frequency="daily", priority="low",  time="18:00"),
        ]}
    )
    sorted_tasks = scheduler.sort_by_time(ascending=False)
    assert sorted_tasks[0].time == "18:00"
    assert sorted_tasks[1].time == "07:30"


def test_sort_by_time_no_tasks_returns_empty():
    """sort_by_time on an empty schedule must return [] without crashing."""
    owner = Owner(name="Alex", available_minutes=60)
    scheduler = Scheduler(owner)
    scheduler.build_schedule()
    assert scheduler.sort_by_time() == []


def test_sort_by_time_midnight_boundary():
    """00:00 must sort before all other times."""
    scheduler = make_scheduler(
        available_minutes=120,
        tasks_by_pet={"Buddy": [
            Task("Night meds", duration=5, frequency="daily", priority="high", time="23:59"),
            Task("Early feed", duration=5, frequency="daily", priority="high", time="00:00"),
        ]}
    )
    sorted_tasks = scheduler.sort_by_time()
    assert sorted_tasks[0].time == "00:00"
    assert sorted_tasks[1].time == "23:59"


# ══════════════════════════════════════════════════════════════════════════════
# 4. filter_tasks — by pet and by status
# ══════════════════════════════════════════════════════════════════════════════

def test_filter_tasks_by_pet_returns_only_that_pets_tasks():
    """filter_tasks(pet_name=) must not return tasks belonging to other pets."""
    owner = Owner(name="Alex", available_minutes=120)
    dog = Pet(name="Buddy", species="dog", age=3)
    cat = Pet(name="Luna",  species="cat", age=2)
    dog.add_task(Task("Walk",    duration=20, frequency="daily", priority="high"))
    cat.add_task(Task("Litter",  duration=10, frequency="daily", priority="high"))
    owner.add_pet(dog)
    owner.add_pet(cat)
    scheduler = Scheduler(owner)
    scheduler.build_schedule()

    buddy_tasks = scheduler.filter_tasks(pet_name="Buddy")
    assert all(t.description == "Walk" for t in buddy_tasks)
    assert not any(t.description == "Litter" for t in buddy_tasks)


def test_filter_tasks_same_description_different_pets():
    """Two pets with identically named tasks must not bleed into each other's filter."""
    owner = Owner(name="Alex", available_minutes=120)
    for pet_name in ("Buddy", "Luna"):
        pet = Pet(name=pet_name, species="dog", age=2)
        pet.add_task(Task("Feed", duration=10, frequency="daily", priority="high"))
        owner.add_pet(pet)
    scheduler = Scheduler(owner)
    scheduler.build_schedule()

    buddy_tasks = scheduler.filter_tasks(pet_name="Buddy")
    luna_tasks  = scheduler.filter_tasks(pet_name="Luna")
    assert len(buddy_tasks) == 1
    assert len(luna_tasks)  == 1
    # They are different Task objects even though the descriptions match
    assert buddy_tasks[0] is not luna_tasks[0]


def test_filter_tasks_unknown_pet_returns_empty():
    """Filtering by a pet name that doesn't exist must return []."""
    scheduler = make_scheduler(
        available_minutes=60,
        tasks_by_pet={"Buddy": [Task("Walk", duration=20, frequency="daily", priority="high")]}
    )
    assert scheduler.filter_tasks(pet_name="NoSuchPet") == []


def test_filter_tasks_by_status_pending():
    """filter_tasks(completed=False) must return only incomplete tasks."""
    scheduler = make_scheduler(
        available_minutes=60,
        tasks_by_pet={"Buddy": [
            Task("Walk",  duration=10, frequency="daily", priority="high"),
            Task("Bath",  duration=10, frequency="weekly", priority="low"),
        ]}
    )
    scheduler.mark_task_complete("Walk")
    pending = scheduler.filter_tasks(completed=False)
    assert all(not t.completed for t in pending)
    assert not any(t.description == "Walk" for t in pending)


def test_filter_tasks_by_status_completed():
    """filter_tasks(completed=True) must return only finished tasks."""
    scheduler = make_scheduler(
        available_minutes=60,
        tasks_by_pet={"Buddy": [
            Task("Walk", duration=10, frequency="daily", priority="high"),
            Task("Bath", duration=10, frequency="weekly", priority="low"),
        ]}
    )
    scheduler.mark_task_complete("Walk")
    done = scheduler.filter_tasks(completed=True)
    assert len(done) == 1
    assert done[0].description == "Walk"


def test_filter_tasks_combined_pet_and_status():
    """filter_tasks(pet_name=, completed=) must apply both filters together."""
    owner = Owner(name="Alex", available_minutes=120)
    dog = Pet(name="Buddy", species="dog", age=3)
    cat = Pet(name="Luna",  species="cat", age=2)
    dog.add_task(Task("Walk",   duration=10, frequency="daily", priority="high"))
    dog.add_task(Task("Bath",   duration=10, frequency="weekly", priority="low"))
    cat.add_task(Task("Litter", duration=10, frequency="daily", priority="high"))
    owner.add_pet(dog)
    owner.add_pet(cat)
    scheduler = Scheduler(owner)
    scheduler.build_schedule()
    scheduler.mark_task_complete("Walk")

    buddy_pending = scheduler.filter_tasks(pet_name="Buddy", completed=False)
    assert len(buddy_pending) == 1
    assert buddy_pending[0].description == "Bath"


# ══════════════════════════════════════════════════════════════════════════════
# 5. detect_conflicts
# ══════════════════════════════════════════════════════════════════════════════

def test_detect_conflicts_same_time_slot_across_pets():
    """Two tasks from different pets at the same time must produce a warning."""
    owner = Owner(name="Alex", available_minutes=120)
    dog = Pet(name="Buddy", species="dog", age=3)
    cat = Pet(name="Luna",  species="cat", age=2)
    dog.add_task(Task("Walk",   duration=20, frequency="daily", priority="high", time="08:00"))
    cat.add_task(Task("Litter", duration=10, frequency="daily", priority="high", time="08:00"))
    owner.add_pet(dog)
    owner.add_pet(cat)
    scheduler = Scheduler(owner)
    scheduler.build_schedule()

    conflicts = scheduler.detect_conflicts()
    assert any("08:00" in msg for msg in conflicts)


def test_detect_conflicts_no_clash_returns_no_time_warning():
    """Tasks at different times must not produce a time-conflict warning."""
    scheduler = make_scheduler(
        available_minutes=60,
        tasks_by_pet={"Buddy": [
            Task("Walk",  duration=10, frequency="daily", priority="high",   time="07:00"),
            Task("Bath",  duration=10, frequency="weekly", priority="medium", time="09:00"),
        ]}
    )
    conflicts = scheduler.detect_conflicts()
    assert not any("Time conflict" in msg for msg in conflicts)


def test_detect_conflicts_never_raises():
    """detect_conflicts must return a list and never raise, even with edge-case data."""
    owner = Owner(name="Alex", available_minutes=10)
    pet = Pet(name="Buddy", species="dog", age=3)
    pet.add_task(Task("Impossible", duration=999, frequency="daily", priority="high"))
    owner.add_pet(pet)
    scheduler = Scheduler(owner)
    scheduler.build_schedule()

    result = scheduler.detect_conflicts()   # must not raise
    assert isinstance(result, list)


def test_detect_conflicts_budget_overload_warning():
    """When total task time exceeds the budget, a time-overload warning must appear."""
    scheduler = make_scheduler(
        available_minutes=10,
        tasks_by_pet={"Buddy": [
            Task("Walk", duration=30, frequency="daily",  priority="high"),
            Task("Bath", duration=30, frequency="weekly", priority="low"),
        ]}
    )
    conflicts = scheduler.detect_conflicts()
    assert any("overload" in msg.lower() for msg in conflicts)


def test_detect_conflicts_duplicate_task_warning():
    """A pet with two tasks sharing the same description must trigger a duplicate warning."""
    owner = Owner(name="Alex", available_minutes=60)
    pet = Pet(name="Buddy", species="dog", age=3)
    pet.add_task(Task("Feed", duration=10, frequency="daily", priority="high"))
    pet.add_task(Task("Feed", duration=10, frequency="daily", priority="high", time="18:00"))
    owner.add_pet(pet)
    scheduler = Scheduler(owner)
    scheduler.build_schedule()

    conflicts = scheduler.detect_conflicts()
    assert any("Duplicate" in msg for msg in conflicts)


# ══════════════════════════════════════════════════════════════════════════════
# 6. Edge cases — empty / boundary states
# ══════════════════════════════════════════════════════════════════════════════

def test_build_schedule_pet_with_no_tasks():
    """A pet with no tasks must not cause build_schedule to crash."""
    owner = Owner(name="Alex", available_minutes=60)
    owner.add_pet(Pet(name="Buddy", species="dog", age=3))
    scheduler = Scheduler(owner)
    assert scheduler.build_schedule() == []


def test_build_schedule_owner_with_no_pets():
    """An owner with no pets must return an empty schedule."""
    owner = Owner(name="Alex", available_minutes=60)
    scheduler = Scheduler(owner)
    assert scheduler.build_schedule() == []


def test_get_recurring_summary_all_as_needed_tasks():
    """If all scheduled tasks are 'as needed', every day in the summary must be empty."""
    scheduler = make_scheduler(
        available_minutes=60,
        tasks_by_pet={"Buddy": [
            Task("Vet", duration=30, frequency="as needed", priority="medium"),
        ]}
    )
    summary = scheduler.get_recurring_summary()
    assert all(summary[day] == [] for day in summary)


def test_get_recurring_summary_weekly_task_only_on_monday():
    """A weekly task must appear on Monday and no other day."""
    scheduler = make_scheduler(
        available_minutes=60,
        tasks_by_pet={"Buddy": [
            Task("Bath", duration=20, frequency="weekly", priority="low"),
        ]}
    )
    summary = scheduler.get_recurring_summary()
    assert len(summary["Monday"]) == 1
    for day in ["Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
        assert summary[day] == []


def test_task_invalid_time_raises_value_error():
    """Creating a Task with a malformed time string must raise ValueError immediately."""
    with pytest.raises(ValueError, match="Invalid time"):
        Task(description="Bad task", duration=10, frequency="daily", priority="high", time="25:00")


def test_task_invalid_duration_raises_value_error():
    """A task with zero or negative duration must be rejected at construction time."""
    with pytest.raises(ValueError):
        Task(description="Bad task", duration=0, frequency="daily", priority="high")


# ══════════════════════════════════════════════════════════════════════════════
# MODULE 2 FOCUS TESTS
# Three behaviors specifically required:
#   A. Sorting correctness  — tasks come back in chronological order
#   B. Recurrence logic     — completing a daily task creates a new one
#   C. Conflict detection   — duplicate start times are flagged
#
# HOW TO READ THESE TESTS (Ask-mode explanations):
#
#   assert statements
#   -----------------
#   Each `assert <expression>` line is the actual check. If the expression is
#   False, pytest stops and reports which line failed. Think of it as asking:
#   "Is this true? If not, fail loudly."
#
#   [t.time for t in result]
#   ------------------------
#   This is a list comprehension — it loops over every Task in `result` and
#   pulls out its .time attribute, giving us a plain list of strings like
#   ["07:30", "09:00", "18:00"] that's easy to compare with ==.
#
#   pytest.raises(ValueError)
#   --------------------------
#   A context manager that *expects* the code inside to raise a ValueError.
#   If no error is raised, the test fails. Used to confirm that bad input is
#   rejected rather than silently accepted.
#
#   any(... for msg in conflicts)
#   -----------------------------
#   `any()` returns True if at least one item in the iterable is truthy.
#   Here it checks whether any warning message contains a specific substring,
#   without caring which position in the list it occupies.
# ══════════════════════════════════════════════════════════════════════════════


# ── A. Sorting Correctness ────────────────────────────────────────────────────

def test_sorting_tasks_returned_in_chronological_order():
    """sort_by_time() must return tasks in earliest-to-latest order regardless
    of the order they were added.

    WHY: Tasks are added in reverse time order (18:00 first, 07:30 last) to
    prove that the sort is doing real work, not just preserving insertion order.
    """
    # Arrange — three tasks added in reverse chronological order on purpose
    scheduler = make_scheduler(
        available_minutes=120,
        tasks_by_pet={"Buddy": [
            Task("Evening walk",  duration=20, frequency="daily",  priority="low",    time="18:00"),
            Task("Afternoon meds",duration=5,  frequency="daily",  priority="medium", time="13:30"),
            Task("Morning feed",  duration=10, frequency="daily",  priority="high",   time="07:30"),
        ]}
    )

    # Act — ask the scheduler to sort by time
    result = scheduler.sort_by_time(ascending=True)

    # Assert — the times must come back in strict ascending order
    # [t.time for t in result] builds ["07:30", "13:30", "18:00"] from the result list
    assert [t.time for t in result] == ["07:30", "13:30", "18:00"]


def test_sorting_two_tasks_same_hour_ordered_by_minute():
    """When two tasks share the same hour, minutes decide the order.

    WHY: String comparison of "09:05" vs "09:30" works fine, but this test
    confirms the int-tuple lambda handles same-hour cases correctly.
    """
    scheduler = make_scheduler(
        available_minutes=60,
        tasks_by_pet={"Buddy": [
            Task("Late morning",  duration=10, frequency="daily", priority="low",  time="09:45"),
            Task("Early morning", duration=10, frequency="daily", priority="high", time="09:05"),
        ]}
    )

    result = scheduler.sort_by_time()
    assert result[0].time == "09:05"
    assert result[1].time == "09:45"


def test_sorting_descending_returns_latest_first():
    """ascending=False must reverse the order so the latest task comes first."""
    scheduler = make_scheduler(
        available_minutes=60,
        tasks_by_pet={"Buddy": [
            Task("Morning", duration=10, frequency="daily", priority="high", time="07:00"),
            Task("Night",   duration=10, frequency="daily", priority="low",  time="21:00"),
        ]}
    )

    result = scheduler.sort_by_time(ascending=False)
    # First item in a descending sort must be the latest time
    assert result[0].time == "21:00"


# ── B. Recurrence Logic ───────────────────────────────────────────────────────

def test_completing_daily_task_creates_new_pending_task():
    """After marking a daily task complete and calling renew_recurring_tasks(),
    the pet must have a new pending copy of that task.

    WHY: Daily tasks like 'Morning feed' happen every day. Once done today,
    tomorrow's instance must be queued automatically so the owner doesn't
    have to re-enter it.
    """
    # Arrange — one daily task on Buddy
    owner = Owner(name="Alex", available_minutes=60)
    pet = Pet(name="Buddy", species="dog", age=3)
    pet.add_task(Task("Morning feed", duration=10, frequency="daily", priority="high", time="08:00"))
    owner.add_pet(pet)
    scheduler = Scheduler(owner)
    scheduler.build_schedule()

    # Act — mark the task done, then renew
    scheduler.mark_task_complete("Morning feed")
    renewed = scheduler.renew_recurring_tasks()

    # Assert — one new task was created and it is pending (not completed)
    assert len(renewed) == 1
    assert renewed[0].description == "Morning feed"
    assert renewed[0].completed is False   # the renewed copy starts fresh


def test_renewed_task_is_a_different_object():
    """The renewed task must be a brand-new object, not the completed original.

    WHY: If renew_recurring_tasks() returned the same object, marking it
    incomplete would erase the completion record — the audit trail would break.
    """
    owner = Owner(name="Alex", available_minutes=60)
    pet = Pet(name="Buddy", species="dog", age=3)
    original = Task("Evening walk", duration=20, frequency="daily", priority="medium", time="18:00")
    pet.add_task(original)
    owner.add_pet(pet)
    scheduler = Scheduler(owner)
    scheduler.build_schedule()

    scheduler.mark_task_complete("Evening walk")
    renewed = scheduler.renew_recurring_tasks()

    # `is not` checks object identity — they must be two separate Task instances
    assert renewed[0] is not original


def test_weekly_task_not_renewed():
    """renew_recurring_tasks() must NOT create a new copy for weekly tasks.

    WHY: A weekly bath completed on Monday shouldn't re-appear on Tuesday.
    Only daily tasks recur every day.
    """
    scheduler = make_scheduler(
        available_minutes=60,
        tasks_by_pet={"Buddy": [
            Task("Weekly bath", duration=20, frequency="weekly", priority="low"),
        ]}
    )
    scheduler.mark_task_complete("Weekly bath")
    renewed = scheduler.renew_recurring_tasks()

    # Weekly tasks must be excluded from automatic renewal
    assert renewed == []


def test_renewing_daily_task_appears_in_next_build_schedule():
    """After renewal, a fresh build_schedule() must include the new pending copy.

    WHY: This is the full end-to-end check — the renewed task is not just
    created; it must actually be picked up by the next scheduling run.
    """
    owner = Owner(name="Alex", available_minutes=60)
    pet = Pet(name="Buddy", species="dog", age=3)
    pet.add_task(Task("Morning feed", duration=10, frequency="daily", priority="high"))
    owner.add_pet(pet)
    scheduler = Scheduler(owner)
    scheduler.build_schedule()

    # Complete today's task and renew
    scheduler.mark_task_complete("Morning feed")
    scheduler.renew_recurring_tasks()

    # Run the scheduler again for "tomorrow"
    scheduler.build_schedule()

    # The new pending copy must be in tomorrow's schedule
    descriptions = [t.description for t in scheduler.scheduled]
    assert "Morning feed" in descriptions


# ── C. Conflict Detection ─────────────────────────────────────────────────────

def test_conflict_detected_for_two_tasks_same_time_same_pet():
    """Two tasks on the same pet at the same time must trigger a conflict warning.

    WHY: A pet can't be walked and bathed simultaneously. The scheduler must
    catch this even when both tasks belong to the same animal.
    """
    owner = Owner(name="Alex", available_minutes=120)
    pet = Pet(name="Buddy", species="dog", age=3)
    pet.add_task(Task("Walk",  duration=20, frequency="daily", priority="high",   time="09:00"))
    pet.add_task(Task("Bath",  duration=30, frequency="weekly", priority="medium", time="09:00"))
    owner.add_pet(pet)
    scheduler = Scheduler(owner)
    scheduler.build_schedule()

    conflicts = scheduler.detect_conflicts()

    # any() returns True if at least one message mentions the clashing time
    assert any("09:00" in msg for msg in conflicts)


def test_conflict_detected_for_two_tasks_same_time_different_pets():
    """Two tasks from different pets sharing a start time must be flagged.

    WHY: The owner can't personally supervise two pets at the same moment,
    so cross-pet clashes matter just as much as same-pet clashes.
    """
    owner = Owner(name="Alex", available_minutes=120)
    dog = Pet(name="Buddy", species="dog", age=3)
    cat = Pet(name="Luna",  species="cat", age=2)
    dog.add_task(Task("Walk",   duration=20, frequency="daily", priority="high", time="07:30"))
    cat.add_task(Task("Litter", duration=10, frequency="daily", priority="high", time="07:30"))
    owner.add_pet(dog)
    owner.add_pet(cat)
    scheduler = Scheduler(owner)
    scheduler.build_schedule()

    conflicts = scheduler.detect_conflicts()

    assert any("07:30" in msg for msg in conflicts)
    # The warning must name both tasks so the owner knows what clashed
    clash_msgs = [msg for msg in conflicts if "07:30" in msg]
    assert any("Walk" in msg and "Litter" in msg for msg in clash_msgs)


def test_no_conflict_when_times_are_different():
    """Tasks at different start times must produce zero time-conflict warnings.

    WHY: A false positive here would flood the owner with useless warnings
    and erode trust in the scheduler's output.
    """
    scheduler = make_scheduler(
        available_minutes=60,
        tasks_by_pet={"Buddy": [
            Task("Morning feed", duration=10, frequency="daily",  priority="high", time="07:00"),
            Task("Evening walk", duration=20, frequency="daily",  priority="high", time="17:00"),
        ]}
    )

    conflicts = scheduler.detect_conflicts()

    # No "Time conflict" message should appear
    assert not any("Time conflict" in msg for msg in conflicts)


def test_conflict_message_contains_pet_names():
    """The conflict warning must name the owning pets, not just the task descriptions.

    WHY: With multiple pets, 'Feed' is ambiguous — the warning must say
    whose feed conflicts with whose so the owner can fix the right schedule.
    """
    owner = Owner(name="Alex", available_minutes=120)
    dog = Pet(name="Buddy", species="dog", age=3)
    cat = Pet(name="Luna",  species="cat", age=2)
    dog.add_task(Task("Feed", duration=10, frequency="daily", priority="high", time="08:00"))
    cat.add_task(Task("Feed", duration=10, frequency="daily", priority="high", time="08:00"))
    owner.add_pet(dog)
    owner.add_pet(cat)
    scheduler = Scheduler(owner)
    scheduler.build_schedule()

    conflicts = scheduler.detect_conflicts()
    clash_msgs = [msg for msg in conflicts if "08:00" in msg]

    # Both pet names must appear somewhere in the conflict message
    assert any("Buddy" in msg for msg in clash_msgs)
    assert any("Luna" in msg for msg in clash_msgs)

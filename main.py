from pawpal_system import Task, Pet, Owner, Scheduler

# --- Setup Owner ---
owner = Owner(name="Alex", available_minutes=120)

# --- Setup Pets ---
dog = Pet(name="Buddy", species="Dog", age=3)
cat = Pet(name="Luna",  species="Cat", age=5)

# --- Add Tasks ---
# NOTE: "Morning walk" (Buddy) and "Clean litter box" (Luna) both use time="08:00"
#       This is intentional — we expect detect_conflicts() to flag the clash.
dog.add_task(Task(description="Morning walk",     duration=20, frequency="daily",     priority="high",   time="07:30"))
dog.add_task(Task(description="Feed breakfast",   duration=10, frequency="daily",     priority="high",   time="08:00"))  # ← clash
dog.add_task(Task(description="Flea treatment",   duration=5,  frequency="as needed", priority="medium", time="11:00"))
dog.add_task(Task(description="Evening walk",     duration=20, frequency="daily",     priority="medium", time="18:00"))

cat.add_task(Task(description="Clean litter box", duration=10, frequency="daily",     priority="high",   time="08:00"))  # ← clash
cat.add_task(Task(description="Vet checkup",      duration=30, frequency="as needed", priority="medium", time="14:30"))
cat.add_task(Task(description="Brush fur",        duration=15, frequency="weekly",    priority="low",    time="16:45"))

# --- Register Pets ---
owner.add_pet(dog)
owner.add_pet(cat)

# --- Build Schedule ---
scheduler = Scheduler(owner)
scheduler.build_schedule()

# ── helpers ──────────────────────────────────────────────────────────────────

def print_section(title: str):
    print()
    print("─" * 55)
    print(f"  {title}")
    print("─" * 55)

def print_tasks(tasks):
    if not tasks:
        print("  (none)")
        return
    for t in tasks:
        status = "✓" if t.completed else "○"
        print(f"  [{status}] {t.time}  {t.description:<22} {t.duration:>3} min  {t.priority}")

# ── Conflict Detection ────────────────────────────────────────────────────────

print("=" * 55)
print("         PAWPAL+ — CONFLICT DETECTION DEMO")
print("=" * 55)

conflicts = scheduler.detect_conflicts()
if conflicts:
    print_section("WARNINGS")
    for warning in conflicts:
        print(f"  ⚠  {warning}")
else:
    print("\n  No conflicts detected.")

# ── Sorting & Filtering ───────────────────────────────────────────────────────

print_section("SORTED BY TIME — earliest first")
print_tasks(scheduler.sort_by_time(ascending=True))

print_section("FILTER — Buddy's tasks")
print_tasks(scheduler.filter_tasks(pet_name="Buddy"))

print_section("FILTER — Luna's tasks")
print_tasks(scheduler.filter_tasks(pet_name="Luna"))

print_section("FILTER — pending tasks only")
print_tasks(scheduler.filter_tasks(completed=False))

print()
print("=" * 55)

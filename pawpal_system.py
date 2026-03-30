from dataclasses import dataclass, field
from typing import Literal


@dataclass
class Task:
    description: str
    duration: int                                               # in minutes
    frequency: Literal["daily", "weekly", "as needed"]
    priority: Literal["low", "medium", "high"]
    time: str = "00:00"                                         # scheduled start time in "HH:MM" format
    completed: bool = False

    def __post_init__(self):
        """Validate that duration is positive and priority/frequency are accepted values."""
        if self.duration <= 0:
            raise ValueError(f"Task duration must be positive, got {self.duration}")
        if self.priority not in ("low", "medium", "high"):
            raise ValueError(f"Invalid priority '{self.priority}'. Must be low, medium, or high.")
        if self.frequency not in ("daily", "weekly", "as needed"):
            raise ValueError(f"Invalid frequency '{self.frequency}'.")
        try:
            h, m = self.time.split(":")
            if not (0 <= int(h) <= 23 and 0 <= int(m) <= 59):
                raise ValueError
        except (ValueError, AttributeError):
            raise ValueError(f"Invalid time '{self.time}'. Expected HH:MM (e.g. '08:30').")

    def mark_complete(self):
        """Mark this task as completed."""
        self.completed = True

    def mark_incomplete(self):
        """Reset this task to incomplete/pending."""
        self.completed = False

    def __str__(self) -> str:
        """Return a human-readable summary of the task."""
        status = "done" if self.completed else "pending"
        return f"{self.description} ({self.duration} min, {self.frequency}, {self.priority} priority, {status})"


@dataclass
class Pet:
    name: str
    species: str
    age: int
    tasks: list[Task] = field(default_factory=list)

    def __post_init__(self):
        """Validate that pet age is non-negative."""
        if self.age < 0:
            raise ValueError(f"Pet age cannot be negative, got {self.age}")

    def add_task(self, task: Task):
        """Append a task to this pet's task list."""
        self.tasks.append(task)

    def remove_task(self, description: str) -> bool:
        """Remove a task by description. Returns True if found and removed."""
        for i, task in enumerate(self.tasks):
            if task.description == description:
                self.tasks.pop(i)
                return True
        return False

    def get_tasks(self) -> list[Task]:
        """Return all tasks assigned to this pet."""
        return self.tasks

    def get_pending_tasks(self) -> list[Task]:
        """Return only tasks that have not yet been completed."""
        return [t for t in self.tasks if not t.completed]

    def total_task_time(self) -> int:
        """Total minutes needed to complete all pending tasks."""
        return sum(t.duration for t in self.get_pending_tasks())

    def __str__(self) -> str:
        """Return a human-readable summary of the pet."""
        return f"{self.name} ({self.species}, age {self.age}) — {len(self.tasks)} task(s)"


class Owner:
    def __init__(self, name: str, available_minutes: int):
        """Initialize an owner with a name and daily time budget in minutes."""
        if available_minutes <= 0:
            raise ValueError(f"available_minutes must be positive, got {available_minutes}")
        self.name = name
        self.available_minutes = available_minutes
        self.pets: list[Pet] = []

    def add_pet(self, pet: Pet):
        """Register a pet under this owner."""
        self.pets.append(pet)

    def remove_pet(self, name: str) -> bool:
        """Remove a pet by name. Returns True if found and removed."""
        for i, pet in enumerate(self.pets):
            if pet.name == name:
                self.pets.pop(i)
                return True
        return False

    def get_all_tasks(self) -> list[Task]:
        """Collect all tasks across all pets."""
        return [task for pet in self.pets for task in pet.get_tasks()]

    def get_all_pending_tasks(self) -> list[Task]:
        """Collect only incomplete tasks across all pets."""
        return [task for pet in self.pets for task in pet.get_pending_tasks()]

    def summary(self) -> str:
        """Return a formatted overview of the owner, their pets, and all tasks."""
        lines = [f"Owner: {self.name} | Available time: {self.available_minutes} min"]
        if not self.pets:
            lines.append("  No pets registered.")
        for pet in self.pets:
            lines.append(f"  {pet}")
            for task in pet.get_tasks():
                lines.append(f"    - {task}")
        return "\n".join(lines)


class Scheduler:
    """The brain of PawPal+. Retrieves, organizes, and manages tasks across all pets."""

    PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
    FREQUENCY_ORDER = {"daily": 0, "weekly": 1, "as needed": 2}

    def __init__(self, owner: Owner):
        """Initialize the scheduler with an owner whose pets and tasks will be scheduled."""
        self.owner = owner
        self.scheduled: list[Task] = []
        self.skipped: list[Task] = []

    def build_schedule(self) -> list[Task]:
        """Retrieve all pending tasks, sort by priority then frequency, fit within available time.
        After the first pass, attempt a second pass to fit any skipped tasks into remaining time."""
        pending = self.owner.get_all_pending_tasks()
        sorted_tasks = sorted(
            pending,
            key=lambda t: (self.PRIORITY_ORDER[t.priority], self.FREQUENCY_ORDER[t.frequency])
        )

        self.scheduled = []
        self.skipped = []
        time_used = 0

        for task in sorted_tasks:
            if time_used + task.duration <= self.owner.available_minutes:
                self.scheduled.append(task)
                time_used += task.duration
            else:
                self.skipped.append(task)

        # Second pass: try to fit skipped tasks into remaining budget
        still_skipped = []
        for task in self.skipped:
            if time_used + task.duration <= self.owner.available_minutes:
                self.scheduled.append(task)
                time_used += task.duration
            else:
                still_skipped.append(task)
        self.skipped = still_skipped

        return self.scheduled

    def mark_task_complete(self, description: str) -> bool:
        """Mark a scheduled task complete by description. Returns True if found."""
        for task in self.scheduled:
            if task.description == description:
                task.mark_complete()
                return True
        return False

    def get_tasks_by_priority(self, priority: Literal["low", "medium", "high"]) -> list[Task]:
        """Return scheduled tasks filtered by the given priority level."""
        return [t for t in self.scheduled if t.priority == priority]

    def get_tasks_by_frequency(self, frequency: Literal["daily", "weekly", "as needed"]) -> list[Task]:
        """Return scheduled tasks filtered by the given frequency."""
        return [t for t in self.scheduled if t.frequency == frequency]

    def get_tasks_sorted_by_duration(self, ascending: bool = True) -> list[Task]:
        """Return scheduled tasks sorted by duration.

        Args:
            ascending: When True (default), shortest tasks come first.
                       When False, longest tasks come first.

        Returns:
            A new sorted list; self.scheduled is not modified.

        Example:
            scheduler.get_tasks_sorted_by_duration()          # 5 min, 10 min, 20 min …
            scheduler.get_tasks_sorted_by_duration(False)     # 30 min, 20 min, 5 min …
        """
        return sorted(self.scheduled, key=lambda t: t.duration, reverse=not ascending)

    def sort_by_time(self, ascending: bool = True) -> list[Task]:
        """Return scheduled tasks sorted by their start time in 'HH:MM' format.

        The lambda splits each time string on ':' and converts both parts to int,
        producing a (hour, minute) tuple that sorted() compares numerically —
        so '09:30' < '10:00' < '14:45' regardless of string length quirks.
        """
        return sorted(
            self.scheduled,
            key=lambda t: tuple(int(part) for part in t.time.split(":")),
            reverse=not ascending
        )

    def get_tasks_by_pet(self, pet_name: str) -> list[Task]:
        """Return scheduled tasks that belong to the named pet.

        Uses object identity (id()) rather than description matching so two
        pets with a task of the same name are never confused.

        Args:
            pet_name: The exact name of a registered pet.

        Returns:
            A list of scheduled Task objects owned by that pet, or an empty
            list if the pet name is not found.
        """
        for pet in self.owner.pets:
            if pet.name == pet_name:
                pet_task_ids = {id(t) for t in pet.get_tasks()}
                return [t for t in self.scheduled if id(t) in pet_task_ids]
        return []

    def get_tasks_by_status(self, completed: bool) -> list[Task]:
        """Return scheduled tasks filtered by completion status.

        Args:
            completed: Pass True to get only finished tasks;
                       pass False to get only pending tasks.

        Returns:
            A filtered list drawn from self.scheduled.
        """
        return [t for t in self.scheduled if t.completed == completed]

    def filter_tasks(
        self,
        pet_name: str | None = None,
        completed: bool | None = None,
    ) -> list[Task]:
        """Return scheduled tasks filtered by pet name, completion status, or both.

        Args:
            pet_name:  When provided, only tasks belonging to that pet are returned.
            completed: When True return only done tasks; when False return only
                       pending tasks; when None (default) both are included.

        Examples:
            scheduler.filter_tasks(pet_name="Buddy")
            scheduler.filter_tasks(completed=False)
            scheduler.filter_tasks(pet_name="Luna", completed=True)
        """
        results = self.scheduled

        if pet_name is not None:
            for pet in self.owner.pets:
                if pet.name == pet_name:
                    pet_task_ids = {id(t) for t in pet.get_tasks()}
                    results = [t for t in results if id(t) in pet_task_ids]
                    break
            else:
                return []

        if completed is not None:
            results = [t for t in results if t.completed == completed]

        return results

    def get_recurring_summary(self) -> dict[str, list[Task]]:
        """Map each day of the week to tasks that recur on that day.

        Daily tasks appear every day; weekly tasks are pinned to Monday;
        'as needed' tasks are excluded (no predictable recurrence).
        """
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        summary: dict[str, list[Task]] = {day: [] for day in days}
        for task in self.scheduled:
            if task.frequency == "daily":
                for day in days:
                    summary[day].append(task)
            elif task.frequency == "weekly":
                summary["Monday"].append(task)
        return summary

    def detect_conflicts(self) -> list[str]:
        """Return a list of conflict/warning messages for the current task set.

        Checks for:
        - Total pending time exceeding the owner's daily budget
        - Individual tasks whose duration alone exceeds the full budget
        - Duplicate task descriptions on the same pet
        - Two or more scheduled tasks sharing the same start time (same or different pets)

        Strategy for time conflicts: bucket all scheduled tasks by their 'time'
        string using a plain dict. Any slot with more than one entry is a clash.
        This is O(n), never raises, and works across pets automatically.
        """
        issues: list[str] = []

        # 1. Total time budget check
        total_pending = sum(t.duration for t in self.owner.get_all_pending_tasks())
        if total_pending > self.owner.available_minutes:
            over = total_pending - self.owner.available_minutes
            issues.append(
                f"Time overload: {total_pending} min of pending tasks exceeds "
                f"{self.owner.available_minutes} min daily budget by {over} min."
            )

        # 2. Per-pet checks (single task too long, duplicate descriptions)
        for pet in self.owner.pets:
            seen: set[str] = set()
            for task in pet.get_tasks():
                if task.duration > self.owner.available_minutes:
                    issues.append(
                        f"'{task.description}' for {pet.name} ({task.duration} min) "
                        f"exceeds the full daily budget ({self.owner.available_minutes} min) "
                        f"and can never be scheduled."
                    )
                if task.description in seen:
                    issues.append(
                        f"Duplicate task '{task.description}' found for {pet.name}."
                    )
                seen.add(task.description)

        # 3. Time-slot conflict detection across all scheduled tasks
        # Build a reverse lookup so conflict messages can name the owning pet.
        task_to_pet: dict[int, str] = {
            id(t): pet.name
            for pet in self.owner.pets
            for t in pet.get_tasks()
        }

        # Bucket scheduled tasks by start time — O(n)
        time_buckets: dict[str, list[Task]] = {}
        for task in self.scheduled:
            time_buckets.setdefault(task.time, []).append(task)

        # Any bucket with more than one task is a conflict
        for slot, clashing in time_buckets.items():
            if len(clashing) > 1:
                names = ", ".join(
                    f"'{t.description}' ({task_to_pet.get(id(t), '?')})"
                    for t in clashing
                )
                issues.append(
                    f"Time conflict at {slot}: {names} are all scheduled at the same time."
                )

        return issues

    def renew_recurring_tasks(self) -> list[Task]:
        """For every completed daily task in the schedule, add a fresh pending
        copy back to its owning pet so the next build_schedule() includes it.

        Weekly and 'as needed' tasks are not renewed automatically — weekly
        tasks recur on the owner's schedule, not daily, and 'as needed' tasks
        have no predictable cadence.

        Returns:
            A list of the newly created Task objects that were added to pets.

        Example:
            scheduler.mark_task_complete("Morning walk")
            renewed = scheduler.renew_recurring_tasks()
            # renewed[0] is a fresh pending copy of "Morning walk"
        """
        task_to_pet: dict[int, Pet] = {
            id(t): pet
            for pet in self.owner.pets
            for t in pet.get_tasks()
        }

        renewed: list[Task] = []
        for task in self.scheduled:
            if task.completed and task.frequency == "daily":
                owner_pet = task_to_pet.get(id(task))
                if owner_pet is not None:
                    fresh = Task(
                        description=task.description,
                        duration=task.duration,
                        frequency=task.frequency,
                        priority=task.priority,
                        time=task.time,
                        completed=False,
                    )
                    owner_pet.add_task(fresh)
                    renewed.append(fresh)
        return renewed

    def total_time_scheduled(self) -> int:
        """Return the total minutes used by all scheduled tasks."""
        return sum(t.duration for t in self.scheduled)

    def explain(self) -> str:
        """Return a human-readable summary of scheduled and skipped tasks with time used."""
        if not self.scheduled:
            return "No tasks scheduled. Run build_schedule() first or check that tasks exist."

        lines = [
            f"Scheduled {len(self.scheduled)} task(s) for {self.owner.name} "
            f"using {self.total_time_scheduled()} of {self.owner.available_minutes} available minutes:\n"
        ]
        for task in self.scheduled:
            lines.append(f"  + {task}")

        if self.skipped:
            lines.append(f"\nSkipped {len(self.skipped)} task(s) due to time constraints:")
            for task in self.skipped:
                lines.append(f"  - {task}")

        return "\n".join(lines)

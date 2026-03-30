# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.

Response: Owner is the person using the app. They have a name and a certain amount of time available in their day. They can register one or more pets and request a schedule based on their tasks.

Pet belongs to an owner. Each pet has basic info like a name, species, and age. A pet can have multiple care tasks associated with it.

Task represents a single care activity — like feeding, a walk, or a vet visit. Each task has a title, how long it takes, and a priority level (low, medium, or high).

Schedule is the output of the app. It looks at all the tasks, compares them against how much time the owner has available, and decides which tasks to include and in what order — prioritizing the most urgent ones first. It can also explain why it made those choices.

- What classes did you include, and what responsibilities did you assign to each?

Response: The design includes four classes, each with a distinct responsibility:

- **Task** — represents a single care activity. It holds the task title, how long it takes (in minutes), and its priority level (low, medium, or high). It is a pure data container with no behavior.

- **Pet** — represents a pet belonging to an owner. It stores the pet's name, species, and age, and maintains a list of associated tasks. It is responsible for organizing care tasks at the pet level.

- **Owner** — represents the person using the app. It stores the owner's name and how many minutes they have available in their day. It holds a list of pets and is responsible for requesting a schedule.

- **Schedule** — represents the output of the planning process. It is responsible for taking a list of tasks and a time limit, deciding which tasks fit, ordering them by priority, and explaining the decisions made.


**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

Response: Yes, several changes were made during implementation after identifying missing relationships and logic bottlenecks:

- **`add_task()` and `add_pet()` were stubs** — both methods were `pass` and never stored data. Fixed by adding `self.tasks.append(task)` and `self.pets.append(pet)` so the objects actually build up state.

- **`Schedule.generate()` ignored its inputs** — the method received tasks and available time but returned an empty list. Fixed by implementing a greedy scheduling algorithm that sorts tasks by priority (high → medium → low) and fits as many as possible within the time budget.

- **`Owner.get_schedule()` was disconnected** — it returned an empty `Schedule()` without passing any tasks or time. Fixed by collecting all tasks from all pets and calling `generate()` with `available_minutes`, closing the chain between owner → pets → tasks → schedule.

- **`priority` changed from `str` to `Literal["low", "medium", "high"]`** — the original plain string type allowed invalid values that would break sorting. Using `Literal` enforces valid inputs at the type level.

- **`Task` and `Pet` were converted to dataclasses** — this eliminated boilerplate `__init__` code and made the data structure cleaner without changing any behavior.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

**Tradeoff: exact time-match conflict detection instead of interval overlap**

The `detect_conflicts()` method flags a conflict only when two tasks share the exact same `time` string (e.g., both set to `"08:00"`). It does *not* check whether one task's time window overlaps another's — for example, a 30-minute task starting at `"08:00"` and a 10-minute task starting at `"08:20"` would not be flagged even though they run concurrently.

Detecting true overlap would require comparing start times against computed end times (`start + duration`), converting `"HH:MM"` strings to total minutes, and checking every pair of tasks — an O(n²) comparison vs. the current O(n) bucket approach.

This tradeoff is reasonable for a daily pet care app because:
1. Tasks like "morning walk" or "feed breakfast" are loosely scheduled reminders, not rigid calendar appointments with hard start/end boundaries.
2. An owner reading the schedule will naturally space tasks out; the exact-match warning catches the most obvious mistake (identical start times) without over-engineering the logic.
3. Keeping the detection simple makes the code easier to read, test, and explain — which matters more at this stage than catching every possible overlap.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

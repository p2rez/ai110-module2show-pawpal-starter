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

Response: The scheduler considers three constraints: **time budget** (owner's available minutes per day), **task priority** (high → medium → low), and **task frequency** (daily → weekly → as needed). Within each priority tier, daily tasks are scheduled before weekly ones, and weekly before "as needed," because a daily feeding matters more than a weekly bath even if both are marked medium priority.

Time budget was the most important constraint to enforce strictly — the scheduler must never overschedule, or the owner loses trust in the output. Priority was next because a pet's medication always matters more than enrichment play. Frequency was a secondary tiebreaker that made the sort feel more natural without requiring the owner to think about it explicitly.

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

Response: AI was used across every phase, but in different roles depending on the task:

- **Design brainstorming** — asking Copilot to review the UML sketch and identify missing relationships caught the disconnected `Owner.get_schedule()` chain before any code was written.
- **Generating algorithmic options** — asking "What is a lightweight conflict detection strategy that returns warnings instead of crashing?" produced multiple approaches (dict bucket, `defaultdict`, `itertools.groupby`) so I could compare tradeoffs before choosing.
- **Writing tests** — using `#codebase` to ask for edge cases surfaced scenarios I hadn't considered, like a pet with no tasks or a task that exactly fills the budget.
- **Docstring generation** — the Generate documentation smart action filled in `Args`, `Returns`, and `Examples` blocks consistently across all new methods.

The most effective prompt pattern was **"Given this constraint, what are my options and their tradeoffs?"** rather than "write this for me." That framing forced AI to explain choices, which made it easier to decide what to actually keep.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

Response: When asking how to simplify the time-bucket loop in `detect_conflicts()`, Copilot offered two alternatives: a `defaultdict(list)` version and an `itertools.groupby` version. The `groupby` approach was the most "Pythonic" — it's a single expression — but it has two hidden gotchas: the input must be pre-sorted first (adding O(n log n) cost) and the group iterator is one-shot, meaning you have to call `list(group)` immediately or lose the data. A student reading that code for the first time would likely miss both issues.

I kept the `setdefault` version because it does exactly one thing per line and requires zero imports. I verified the decision by asking: *"Would someone new to Python understand what this does in 10 seconds?"* The `setdefault` version passes that test; `groupby` does not. The AI suggestion was clever — it just wasn't the right tool for a learning-focused project where readability matters more than terseness.

**c. VS Code Copilot — AI strategy reflection**

*Which Copilot features were most effective for building your scheduler?*

Three features stood out:

1. **Inline Chat on specific methods** — highlighting `build_schedule()` or `detect_conflicts()` and asking a focused question kept the AI's context tight. It answered about that method specifically rather than guessing what the broader system did.

2. **`#codebase` in Copilot Chat** — attaching the whole codebase let me ask cross-cutting questions like "what edge cases should I test for sorting and recurring tasks?" and get answers that were grounded in the actual class structure rather than generic advice.

3. **Generate documentation smart action** — adding full docstrings to all new methods in one pass, consistent in format across every method, would have taken significantly longer to write by hand. The AI maintained the same `Args` / `Returns` / `Example` structure throughout without being reminded.

*Give one example of an AI suggestion you rejected or modified to keep your system design clean.*

When asking how to simplify the time-bucket loop, Copilot suggested `itertools.groupby` as the most Pythonic approach. It's terse and idiomatic, but it requires sorting the input first and consumes the group iterator in a single pass — two non-obvious behaviors that make the code harder to read for anyone learning Python. I kept the `dict.setdefault` version because it is explicit, requires no imports, and does exactly one thing per line. The AI suggestion was technically correct; it just wasn't the right choice for this project's audience and goals.

*How did using separate chat sessions for different phases help you stay organized?*

Each session had a single job. The design session focused on class structure and UML gaps. The testing session — started fresh, with no memory of implementation decisions — generated edge cases from first principles rather than just confirming what the code already did. The documentation session had no scheduling context to distract it. If all of that had been one continuous conversation, earlier answers would have colored later ones: the testing AI would have "known" the implementation and been less likely to challenge it. Separate sessions enforced separation of concerns at the AI collaboration level, mirroring the same principle the code was built on.

*Summarize what you learned about being the "lead architect" when collaborating with powerful AI tools.*

AI accelerated every mechanical part of the build — generating options, writing boilerplate, expanding tests, formatting docstrings. But the decisions that determined the system's quality were human ones: which abstraction boundary to draw, which suggestion to reject because it was clever but unreadable, which edge case mattered enough to test. The lead architect's job is not to write every line — it is to hold the vision of what the system should be and filter everything else through that vision. AI makes that job faster only when you stay in the driver's seat. The moment you stop questioning suggestions and start accepting them, you stop being the architect and become an editor of someone else's design.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

Response: The final suite covers 37 tests across eight behavioral groups: `build_schedule` priority ordering and time budget enforcement, `sort_by_time` chronological correctness (including same-hour minute-level ordering and the midnight boundary), `filter_tasks` pet isolation using object identity, completion status filtering, and combined filters, `detect_conflicts` same-time clashes across pets, false-positive prevention, and warning message content, `renew_recurring_tasks` recurrence logic, and edge cases like empty pets, owners with no pets, and validation errors.

These tests mattered because the scheduler's value to a pet owner depends entirely on correctness — a schedule that silently over-books the owner's time or misattributes a task to the wrong pet is worse than no schedule at all. The tests made each algorithmic change safe to ship by catching regressions immediately.

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

Response: **4 out of 5.** The core logic — prioritization, time budget, sorting, filtering, conflict detection, and recurrence — is fully covered and all 37 tests pass consistently. One star is withheld because the Streamlit UI layer has no automated tests. The wiring between widgets and `Scheduler` methods is exercised manually only, which means a UI regression could go undetected.

If given more time, the next edge cases to test would be: (1) an owner who modifies `available_minutes` mid-session and whether the existing schedule is correctly invalidated, (2) `renew_recurring_tasks` called twice without rebuilding the schedule — does it create duplicate copies?, and (3) a pet whose task list grows very large (100+ tasks) to confirm the O(n) conflict detection holds its performance guarantee in practice.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

Response: The part I'm most satisfied with is the `detect_conflicts()` method and its test coverage. It handles four distinct problem types (time overload, tasks too long to schedule, duplicates, and same-slot clashes), returns plain strings instead of raising exceptions, and does it all in O(n) using a single dict-bucket pass. Writing the tests for it first — asking "what should this return for each case?" — forced the implementation to be precise rather than approximate. Seeing all four conflict types surface correctly in the Streamlit UI as color-coded warnings, with actionable tips for each, felt like the moment the app became genuinely useful rather than just functional.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

Response: I would add **true interval-overlap detection** to `detect_conflicts()`. The current exact-match approach catches the most obvious mistake but misses cases like a 30-minute task at 8:00 and a 10-minute task at 8:20. Fixing this requires converting `"HH:MM"` strings to integer minutes, computing each task's end time (`start + duration`), and checking pairs — an O(n²) scan that's acceptable at the scale of a daily pet schedule (rarely more than 20 tasks). I would also add at least one Streamlit UI test using `streamlit.testing` so the full stack is covered, not just the business logic.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

Response: The most important thing I learned is that **AI is a force multiplier, not a decision maker** — and that distinction determines whether the output is good or just fast.

Every time I asked Copilot a broad question like "write my conflict detection," I got code that technically worked but didn't fit the project's constraints (wrong complexity, wrong error strategy, or the wrong level of abstraction for a student codebase). Every time I asked a narrow question like "what are my options for grouping tasks by start time, and what are the tradeoffs of each?" I got information I could reason about and decide from.

Using separate chat sessions for design, testing, and documentation kept each conversation focused and prevented earlier context from contaminating later decisions. When the testing session didn't know about the implementation session, it generated edge cases from first principles rather than just validating what already existed.

Being the "lead architect" meant that every suggestion had to pass through my judgment before it touched the code: Does this fit the class's responsibility? Is it readable for someone learning Python? Does it introduce a hidden dependency? AI made me faster at all the mechanical parts — generating options, writing boilerplate, expanding docstrings — but the decisions that shaped the system's structure were mine. That's the skill that scales beyond any single tool.

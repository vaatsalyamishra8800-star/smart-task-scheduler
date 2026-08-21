# Smart Task Scheduler (CLI)

A command-line task manager that schedules tasks by **priority and deadline**,
instead of just listing them in the order they were added — like a simplified
version of how an OS scheduler or a real task-queue system decides what runs next.

## Why this project

I built this to apply core data structures and algorithms to something
beyond a textbook problem — practicing not just implementation, but *why*
each structure was the right choice for the job.

## Data Structures Used

| Structure       | Used for                          | Why                                                              |
|------------------|-----------------------------------|-------------------------------------------------------------------|
| Min-Heap (`heapq`) | Fetching the most urgent task    | O(log n) insert and pop vs. O(n) for a sorted list                |
| Hash Map (`dict`)  | Looking up/updating tasks by ID  | O(1) access instead of scanning every task                        |
| Stack (`list`)     | Undo functionality               | Last-in-first-out matches "undo the most recent action" naturally |
| JSON file          | Persistence between runs         | Tasks survive after the program closes                            |

## Features

- Add tasks with a priority (1–5) and a deadline
- Automatically surface the single most urgent task
- Mark tasks complete or cancel them
- Undo the last add / complete / cancel action
- Tasks persist across sessions (saved to `tasks.json`)

## How to Run

```bash
python3 task_scheduler.py
```

Then use any of the commands:

```
add              -> add a new task (prompts for name, priority, deadline)
list             -> show all tasks, most urgent first
next             -> show only the single most urgent task
complete <id>    -> mark a task done
cancel <id>      -> remove a task
undo             -> undo the last action
help             -> show all commands
exit             -> quit
```

## Example

```
> add
Task name: Finish assignment
Priority (1=highest, 5=lowest): 1
Deadline (YYYY-MM-DD): 2026-08-25
Added: [1] Finish assignment | priority=1 | deadline=2026-08-25 | pending

> next
[1] Finish assignment | priority=1 | deadline=2026-08-25 | pending
```

## What I'd Improve Next

- Add tags/categories for tasks
- Support recurring tasks
- Add a simple web UI on top of the same scheduling logic

## Tech

Python 3, standard library only (`heapq`, `json`, `datetime`, `itertools`) —
no external dependencies.

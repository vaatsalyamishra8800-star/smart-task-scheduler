"""
Smart Task Scheduler (CLI)
---------------------------
A command-line task manager that schedules tasks by priority and deadline,
instead of just listing them in the order they were added.

Data structures used:
    - Min-heap (heapq)  -> always fetch the most urgent task in O(log n)
    - Hash map (dict)   -> look up / update / cancel any task by ID in O(1)
    - Stack (list)      -> undo the last action (add / complete / cancel)
    - JSON file         -> persist tasks between runs

Author: Vaatsalya Mishra
"""

import heapq
import json
import os
from datetime import datetime
from itertools import count

DATA_FILE = "tasks.json"


class Task:
    """A single task with a priority and a deadline."""

    def __init__(self, task_id, name, priority, deadline, status="pending"):
        self.id = task_id
        self.name = name
        self.priority = priority          # 1 = highest priority, 5 = lowest
        self.deadline = deadline          # string in YYYY-MM-DD format
        self.status = status              # "pending" or "done"

    def sort_key(self):
        """
        Lower value = more urgent.
        Tasks are ordered first by priority, then by how close the
        deadline is. This is the value pushed into the heap.
        """
        try:
            days_left = (datetime.strptime(self.deadline, "%Y-%m-%d") - datetime.now()).days
        except ValueError:
            days_left = 9999  # invalid/no deadline sinks to the bottom
        return (self.priority, days_left)

    def to_dict(self):
        return self.__dict__

    def __str__(self):
        return f"[{self.id}] {self.name} | priority={self.priority} | deadline={self.deadline} | {self.status}"


class TaskScheduler:
    def __init__(self):
        self.heap = []                 # min-heap of (sort_key, id) — the priority queue
        self.tasks = {}                # id -> Task, for O(1) lookup
        self.action_stack = []         # stack of past actions, for undo
        self._id_counter = count(1)
        self._load()

    # ---------- core operations ----------

    def add_task(self, name, priority, deadline, record_action=True):
        task_id = next(self._id_counter)
        task = Task(task_id, name, priority, deadline)
        self.tasks[task_id] = task
        heapq.heappush(self.heap, (task.sort_key(), task_id))

        if record_action:
            self.action_stack.append(("add", task_id))
        self._save()
        return task

    def get_next_task(self):
        """Peek at the most urgent pending task without removing it."""
        self._clean_heap()
        if not self.heap:
            return None
        _, task_id = self.heap[0]
        return self.tasks[task_id]

    def complete_task(self, task_id, record_action=True):
        task = self.tasks.get(task_id)
        if not task or task.status == "done":
            return False
        task.status = "done"
        if record_action:
            self.action_stack.append(("complete", task_id))
        self._save()
        return True

    def cancel_task(self, task_id, record_action=True):
        if task_id not in self.tasks:
            return False
        removed_task = self.tasks.pop(task_id)
        if record_action:
            self.action_stack.append(("cancel", removed_task))
        self._save()
        return True

    def undo(self):
        """Pop the last action off the stack and reverse it."""
        if not self.action_stack:
            print("Nothing to undo.")
            return

        action, payload = self.action_stack.pop()

        if action == "add":
            self.tasks.pop(payload, None)
            print(f"Undid: add task {payload}")
        elif action == "complete":
            if payload in self.tasks:
                self.tasks[payload].status = "pending"
            print(f"Undid: complete task {payload}")
        elif action == "cancel":
            task = payload
            self.tasks[task.id] = task
            heapq.heappush(self.heap, (task.sort_key(), task.id))
            print(f"Undid: cancel task {task.id}")

        self._save()

    def list_tasks(self):
        self._clean_heap()
        if not self.tasks:
            print("No tasks yet.")
            return
        # Show tasks sorted by urgency without destroying the heap
        ordered = sorted(self.tasks.values(), key=lambda t: t.sort_key())
        for task in ordered:
            print(task)

    # ---------- internal helpers ----------

    def _clean_heap(self):
        """Remove stale/completed/cancelled entries sitting at the top of the heap."""
        while self.heap:
            _, task_id = self.heap[0]
            task = self.tasks.get(task_id)
            if task is None or task.status == "done":
                heapq.heappop(self.heap)
            else:
                break

    def _save(self):
        data = {
            "tasks": [t.to_dict() for t in self.tasks.values()],
            "next_id": next(self._id_counter),
        }
        # restore the counter after peeking at it
        self._id_counter = count(data["next_id"])
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def _load(self):
        if not os.path.exists(DATA_FILE):
            return
        with open(DATA_FILE, "r") as f:
            data = json.load(f)

        max_id = 0
        for t in data.get("tasks", []):
            task = Task(t["id"], t["name"], t["priority"], t["deadline"], t["status"])
            self.tasks[task.id] = task
            max_id = max(max_id, task.id)
            if task.status != "done":
                heapq.heappush(self.heap, (task.sort_key(), task.id))

        self._id_counter = count(max_id + 1)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

HELP = """
Commands:
  add          Add a new task
  list         Show all tasks, most urgent first
  next         Show the single most urgent task
  complete <id>  Mark a task as done
  cancel <id>    Remove a task entirely
  undo         Undo the last add/complete/cancel
  help         Show this message
  exit         Quit
"""


def main():
    scheduler = TaskScheduler()
    print("Smart Task Scheduler — type 'help' for commands.")

    while True:
        raw = input("\n> ").strip()
        if not raw:
            continue
        parts = raw.split()
        cmd = parts[0].lower()

        if cmd == "add":
            name = input("Task name: ").strip()
            priority = int(input("Priority (1=highest, 5=lowest): ").strip() or 3)
            deadline = input("Deadline (YYYY-MM-DD): ").strip()
            task = scheduler.add_task(name, priority, deadline)
            print(f"Added: {task}")

        elif cmd == "list":
            scheduler.list_tasks()

        elif cmd == "next":
            task = scheduler.get_next_task()
            print(task if task else "No pending tasks.")

        elif cmd == "complete" and len(parts) > 1:
            ok = scheduler.complete_task(int(parts[1]))
            print("Marked complete." if ok else "Task not found.")

        elif cmd == "cancel" and len(parts) > 1:
            ok = scheduler.cancel_task(int(parts[1]))
            print("Cancelled." if ok else "Task not found.")

        elif cmd == "undo":
            scheduler.undo()

        elif cmd == "help":
            print(HELP)

        elif cmd == "exit":
            print("Goodbye!")
            break

        else:
            print("Unknown command. Type 'help' for options.")


if __name__ == "__main__":
    main()

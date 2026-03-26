from dataclasses import dataclass, field


@dataclass
class Task:
    title: str
    duration: int       # in minutes
    priority: str       # "low", "medium", "high"


@dataclass
class Pet:
    name: str
    species: str
    age: int
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task):
        pass

    def get_tasks(self) -> list[Task]:
        return self.tasks


class Schedule:
    def __init__(self):
        self.tasks: list[Task] = []

    def generate(self, tasks: list[Task], available_time: int) -> list[Task]:
        return self.tasks

    def explain(self) -> str:
        return ""


class Owner:
    def __init__(self, name: str, available_minutes: int):
        self.name = name
        self.available_minutes = available_minutes
        self.pets: list[Pet] = []

    def add_pet(self, pet: Pet):
        pass

    def get_schedule(self) -> Schedule:
        return Schedule()

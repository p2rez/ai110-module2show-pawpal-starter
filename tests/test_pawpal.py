from pawpal_system import Task, Pet


def test_mark_complete_changes_status():
    task = Task(description="Morning walk", duration=20, frequency="daily", priority="high")
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_add_task_increases_pet_task_count():
    pet = Pet(name="Buddy", species="Dog", age=3)
    assert len(pet.get_tasks()) == 0
    pet.add_task(Task(description="Feed breakfast", duration=10, frequency="daily", priority="high"))
    assert len(pet.get_tasks()) == 1

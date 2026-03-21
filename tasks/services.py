from .models import Task

class TaskRepository:
    @staticmethod
    def get_all_tasks():
        return Task.objects.all().order_by('-created_at')

    @staticmethod
    def get_task_by_id(task_id):
        try:
            return Task.objects.get(id=task_id)
        except Task.DoesNotExist:
            return None

    @staticmethod
    def update_task_status(task, status):
        task.status = status
        task.save(update_fields=['status'])
        return task

class TaskService:
    @staticmethod
    def get_all_tasks():
        return TaskRepository.get_all_tasks()

    @staticmethod
    def get_task_by_id(task_id):
        return TaskRepository.get_task_by_id(task_id)

    @staticmethod
    def cancel_task(task_id):
        task = TaskRepository.get_task_by_id(task_id)
        if not task:
            return False
        TaskRepository.update_task_status(task, "CANCELLED")
        return True

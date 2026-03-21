from django.apps import AppConfig
import threading


class TasksConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tasks'

    def ready(self):
        from worker.worker import run_worker
        threading.Thread(target=run_worker, daemon=True).start()
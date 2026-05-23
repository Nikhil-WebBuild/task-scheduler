from django.apps import AppConfig
import threading


class TasksConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tasks'

    def ready(self):
        from worker.worker import run_worker

        # Start the background worker in a separate daemon thread.
        # daemon=True ensures the thread shuts down automatically when the Django process exits.
        threading.Thread(target=run_worker, daemon=True).start()
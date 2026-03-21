import time
import requests
from datetime import timedelta

from django.utils.timezone import now
from django.db import transaction
from tasks.models import Task

def handle_failure(task, error_msg):
    task.retry_count += 1
    if task.retry_count >= task.max_retries:
        task.status = "FAILED"
        print(f"❌ Task {task.id} failed permanently: {error_msg}")
    else:
        task.status = "PENDING"
        # Exponential backoff: 5, 15, 45 mins
        delay_minutes = 5 * (3 ** (task.retry_count - 1))
        task.execute_at = now() + timedelta(minutes=delay_minutes)
        print(f"⚠️ Task {task.id} failed, retrying in {delay_minutes} mins. Attempt {task.retry_count}/{task.max_retries} ({error_msg})")
        
    task.last_attempt = now()
    task.save(update_fields=["status", "retry_count", "execute_at", "last_attempt"])

def run_worker():
    print("🚀 Worker started...")

    while True:
        current_time = now()
        task = None
        
        # We need an atomic transaction to lock the rows
        try:
            with transaction.atomic():
                # Fetch ONE pending task ready to execute, locking it so no other worker picks it
                tasks = Task.objects.select_for_update(skip_locked=True).filter(
                    status="PENDING",
                    execute_at__lte=current_time
                )[:1]

                if tasks:
                    task = tasks[0]
                    # Mark as running immediately
                    task.status = "RUNNING"
                    task.save(update_fields=["status"])
        except Exception as db_e:
            print(f"Database error while fetching tasks: {db_e}")
            time.sleep(5)
            continue

        if task:
            print(f"⚡ Executing task {task.id}")
            
            try:
                response = requests.post(
                    task.url,
                    json=task.payload,
                    timeout=5
                )

                if response.status_code == 200:
                    task.status = "SUCCESS"
                    task.last_attempt = now()
                    task.save(update_fields=["status", "last_attempt"])
                    print(f"✅ Task {task.id} completed")
                else:
                    handle_failure(task, f"status {response.status_code}")

            except Exception as e:
                handle_failure(task, str(e))
                
        else:
            time.sleep(5)  # No tasks ready, wait 5 seconds

if __name__ == "__main__":
    run_worker()
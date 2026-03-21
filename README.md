# Scheduled Notification Service (NexTask)

A distributed background service for scheduling and executing time-delayed webhooks and notifications. Built with Django, PostgreSQL, and a standalone Background Worker process.

## 🚀 Features
- **REST API & Web UI Dashboard**: Complete control over your scheduled tasks via the modern Web UI or raw APIs.
- **Asynchronous Execution**: The API responds instantly while a separate worker process handles execution.
- **Robust Error Handling**: External HTTP call failures trigger an exponential backoff retry mechanism (5, 15, 45 mins).
- **Concurrency Safe**: Uses PostgreSQL row-level locking (`select_for_update(skip_locked=True)`) to prevent duplicate execution across multiple workers.
- **Containerized**: Full Docker Compose setup for instant deployment.

---

## 🏗️ Architecture & Service Communication Flow

The system acts as an intermediary layer between your client and external APIs.

1. **User Client / Dashboard** submits a new Task (`URL`, `time`, JSON `payload`) to the **Django REST API**.
2. **API** validates the request and creates a record in the **PostgreSQL Database** with a `PENDING` status.
3. **Background Worker** (an infinite polling script) continuously checks the database for `PENDING` tasks where the execution time has arrived (`execute_at <= current_time`).
4. The **Worker** locks the specific database row to prevent other workers from fetching it simultaneously.
5. The **Worker** makes the HTTP POST request (Webhook) to the target **External Target URL**.
6. Depending on the HTTP response (200 OK vs 4xx/5xx), the Worker updates the task status in the DB to `SUCCESS` or initiates a retry leading to `FAILED`.

---

## 📊 Database Schema (`Task` Model)

The central piece of data storage is the `Task` relational table.

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary Key (Secure unique identifier). |
| `url` | URLField | The target API endpoint to hit. |
| `payload` | JSONField | The JSON data payload to send to the target URL. |
| `status` | CharField | Current state (`PENDING`, `RUNNING`, `SUCCESS`, `FAILED`, `CANCELLED`). Indexed for extremely fast query lookups. |
| `execute_at` | DateTimeField | The scheduled time for execution. Indexed for background polling bounds. |
| `retry_count` | IntegerField | Tracks how many times execution has failed. |
| `max_retries` | IntegerField | Configured upper limit (default: 3). |

---

## ⚙️ Explanation of Scheduling and Worker Logic

The system is fully decoupled. The API handles high-throughput ingestions but does not execute the webhooks itself.

- **Polling Loop**: The worker (`worker.py`) loops indefinitely, querying indexed database columns every 5 seconds without consuming heavy CPU.
- **Row Locking**: It uses `select_for_update(skip_locked=True)` in an atomic transactional block. This entirely prevents race conditions. Even if 10 worker containers are booted up simultaneously, a single task is guaranteed to only be processed by exactly one worker.
- **Exponential Backoff**: If the external target URL is offline or unresponsive, the worker catches the error, increments `retry_count`, and alters the next `execute_at` based on the formula `5 * (3 ^ (retry_count - 1))` minutes. This means failures are retried after 5 minutes, 15 minutes, and then 45 minutes before failing permanently.

---

## 📘 How to Run & Use the Project

You can run this project locally with Docker or via a Python virtual environment.

### Option 1: Docker (Recommended)
1. Ensure Docker Desktop is running on your machine.
2. Run `docker-compose up --build -d` in your terminal. This fires up the Postgres DB, API Server, and Worker.
3. Access the powerful Web UI Dashboard at `http://localhost:8000`.

### Option 2: Run Locally (Python 3.10+)
If you prefer running without Docker for development:
1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```
2. Install the necessary packages:
   ```bash
   pip install -r requirements.txt
   ```
3. Run migrations and create a user account for testing:
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```
4. **Open Terminal 1**: `python manage.py runserver 8000` (Starts Web UI and REST APIs).
5. **Open Terminal 2**: `python worker/worker.py` (Starts the infinite task engine).

### Using the APIs directly (Postman)
If you do not want to use the UI dashboard, you can trigger APIs manually.
- **Get Token**: `POST /api/token/` (Provide JSON `{"username":"...", "password":"..."}`)
- **Schedule Task**: `POST /api/tasks/`
  ```json
  POST /api/tasks/
  Authorization: Bearer <your_jwt_token>

  {
      "url": "https://httpbin.org/post",
      "payload": {"message": "hello!"},
      "execute_at": "2026-03-21T18:00:00Z"
  }
  ```

---

## 📈 Scaling Considerations

1. **Horizontal Worker Scaling**: Because of the `skip_locked=True` database constraint, you can scale horizontally instantly without clashes. Simply `docker-compose up --scale worker=5` to run 5 instances based on throughput load.
2. **Database Sharding/Partitioning**: As the `Task` table grows massively over months, past-completed tasks should be archived or table-partitioned functionally (e.g., partitioned by month of `created_at`) to keep the polling index B-trees small, preventing the Postgres query from slowing down.
3. **Move to a Distributed Message Queue**: If millisecond-precision triggers or massive global throughputs (>10,000 req/sec) are required, polling Postgres natively is suboptimal. The pure python Worker logic can be easily migrated to `Celery` + `RabbitMQ/Redis` backend while keeping the REST Controller APIs completely identical.

---

## 💡 Real-World Use Cases (Examples)

If you are wondering what kind of `url` and `payload` to send to this service, here are two practical examples of how companies use scheduled webhook services:

### Example 1: E-commerce "Abandoned Cart" Email
When a user leaves items in their shopping cart, your main backend schedules an email to be sent exactly 24 hours later with a discount code.
- **`url`**: `https://api.sendgrid.com/v3/mail/send` (Your Email Provider's API)
- **`payload`**: 
  ```json
  {
    "personalizations": [{"to": [{"email": "customer@example.com"}]}],
    "subject": "You forgot your shoes! Here is a 10% discount.",
    "content": [{"type": "text/plain", "value": "Use code SAVE10 at checkout."}]
  }
  ```
- **`execute_at`**: `2026-03-22T14:30:00Z` (Tomorrow, exactly 24 hours later)
- **Result**: Your main server doesn't wait 24 hours. It offloads the task to the Scheduler, which automatically triggers the SendGrid API at the correct time.

### Example 2: WhatsApp Appointment Reminder
A user books a doctor's appointment for Friday at 10:00 AM. You want the system to send them an automatic WhatsApp reminder on Friday at 8:00 AM.
- **`url`**: `https://api.twilio.com/2010-04-01/Accounts/.../Messages.json` (WhatsApp/SMS API)
- **`payload`**: 
  ```json
  {
    "To": "whatsapp:+919876543210",
    "Body": "Reminder: Your appointment is in 2 hours at 10:00 AM."
  }
  ```
- **`execute_at`**: `2026-03-25T08:00:00Z` (Friday, 8:00 AM)
- **Result**: The background worker securely holds the task and executes the HTTP POST request right when Friday 8:00 AM arrives.

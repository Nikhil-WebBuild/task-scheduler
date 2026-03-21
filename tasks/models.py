import uuid
from django.db import models

class Task(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('RUNNING', 'Running'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    url = models.TextField()
    payload = models.JSONField()

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', db_index=True)

    execute_at = models.DateTimeField(db_index=True)

    retry_count = models.IntegerField(default=0)
    max_retries = models.IntegerField(default=3)

    last_attempt = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.id)
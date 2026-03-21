from django.contrib import admin
from .models import Task

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'url', 'status', 'execute_at', 'retry_count')
    list_filter = ('status',)
    search_fields = ('url',)

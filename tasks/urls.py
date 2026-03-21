from django.urls import path
from .views import TaskCreateView

urlpatterns = [
    path('tasks/', TaskCreateView.as_view()),
    path('tasks/<uuid:task_id>/', TaskCreateView.as_view()),
]
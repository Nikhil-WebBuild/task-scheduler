from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import TaskSerializer
from rest_framework.permissions import IsAuthenticated
from .services import TaskService

class TaskCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, task_id=None):
        if task_id:
            task = TaskService.get_task_by_id(task_id)
            if not task:
                return Response({"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND)
            serializer = TaskSerializer(task)
            return Response(serializer.data)
            
        tasks = TaskService.get_all_tasks()
        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data)

    def post(self, request, task_id=None):
        if task_id:
            return Response({"error": "Method not allowed"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
            
        serializer = TaskSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, task_id=None):
        if not task_id:
            return Response({"error": "Task ID is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        success = TaskService.cancel_task(task_id)
        if success:
            return Response({"message": "Task cancelled successfully"})
        return Response({"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND)
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Workflow
from .serializers import WorkflowSerializer


class WorkflowViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing workflows.
    
    - list: Get all workflows
    - create: Create a new workflow
    - retrieve: Get workflow details
    - update/partial_update: Update workflow
    - destroy: Delete workflow
    """
    queryset = Workflow.objects.all()
    serializer_class = WorkflowSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        """Set created_by to current user"""
        serializer.save(created_by=self.request.user)
    
    def get_queryset(self):
        """Filter workflows by current user or if user is admin"""
        user = self.request.user
        if user.is_staff:
            return Workflow.objects.all()
        return Workflow.objects.filter(created_by=user)

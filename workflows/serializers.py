from rest_framework import serializers
from .models import Workflow


class WorkflowSerializer(serializers.ModelSerializer):
    """Serializer for Workflow model"""
    
    created_by_email = serializers.CharField(source='created_by.email', read_only=True)
    
    class Meta:
        model = Workflow
        fields = ['id', 'name', 'description', 'created_by', 'created_by_email', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

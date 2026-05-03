from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Workflow(models.Model):
    """Workflow model for managing document processing workflows"""
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='workflows')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['created_by']),
        ]
    
    def __str__(self):
        return self.name

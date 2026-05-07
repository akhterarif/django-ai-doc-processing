from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Document(models.Model):
    STATUS_CHOICES = [
        ('UPLOADED', 'Uploaded'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]
    
    file = models.FileField(upload_to='documents/')
    file_name = models.CharField(max_length=255, blank=True)
    file_size = models.PositiveBigIntegerField(default=0)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='UPLOADED')
    doc_type = models.CharField(max_length=100, null=True, blank=True)
    summary = models.TextField(blank=True)
    key_points = models.JSONField(default=list)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['uploaded_by']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"Document {self.id} - {self.status}"


class DocumentAnalysis(models.Model):
    document = models.OneToOneField(Document, on_delete=models.CASCADE)
    summary = models.TextField(blank=True)
    key_points = models.JSONField(default=list)
    topics = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Analysis for Document {self.document.id}"


class ChatConversation(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]
    
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='conversations')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.TextField()
    answer = models.TextField(blank=True)
    sources = models.JSONField(default=list)  # Store chunk references
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['document', 'user']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"Chat {self.id} - {self.status} - {self.question[:50]}..."

from django.db import models

class Document(models.Model):
    STATUS_CHOICES = [
        ('uploaded', 'Uploaded'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    file = models.FileField(upload_to='documents/')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='uploaded')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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

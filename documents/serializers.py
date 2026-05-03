from rest_framework import serializers
from .models import Document, DocumentAnalysis


class DocumentSerializer(serializers.ModelSerializer):
    """Serializer for Document model"""
    uploaded_by_email = serializers.CharField(source='uploaded_by.email', read_only=True)
    
    class Meta:
        model = Document
        fields = ['id', 'file', 'uploaded_by', 'uploaded_by_email', 'created_at', 'status', 'doc_type', 'summary', 'key_points']
        read_only_fields = ['id', 'uploaded_by', 'uploaded_by_email', 'created_at', 'status', 'summary', 'key_points']


class DocumentAnalysisSerializer(serializers.ModelSerializer):
    """Serializer for DocumentAnalysis model"""
    
    class Meta:
        model = DocumentAnalysis
        fields = ['document', 'summary', 'key_points', 'topics', 'created_at']
        read_only_fields = ['document', 'created_at']
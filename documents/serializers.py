from rest_framework import serializers
from .models import Document, DocumentAnalysis

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ['id', 'file', 'status', 'created_at', 'updated_at']
        read_only_fields = ['id', 'status', 'created_at', 'updated_at']

class DocumentAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentAnalysis
        fields = ['document', 'summary', 'key_points', 'topics', 'created_at']
        read_only_fields = ['document', 'created_at']
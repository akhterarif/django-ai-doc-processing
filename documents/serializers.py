from rest_framework import serializers
from .models import Document, DocumentAnalysis, ChatConversation


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


class ChatConversationSerializer(serializers.ModelSerializer):
    """Serializer for ChatConversation model"""
    user_email = serializers.CharField(source='user.email', read_only=True)
    document_title = serializers.CharField(source='document.file.name', read_only=True)
    
    class Meta:
        model = ChatConversation
        fields = ['id', 'document', 'document_title', 'user', 'user_email', 'question', 'answer', 'sources', 'status', 'created_at', 'updated_at']
        read_only_fields = ['id', 'document', 'document_title', 'user', 'user_email', 'answer', 'sources', 'status', 'created_at', 'updated_at']
from django.contrib import admin
from .models import Document, DocumentAnalysis, ChatConversation

# Register your models here.

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['id', 'file', 'uploaded_by', 'status', 'doc_type', 'created_at']
    list_filter = ['status', 'doc_type', 'created_at']
    search_fields = ['file', 'uploaded_by__email']
    readonly_fields = ['id', 'created_at']


@admin.register(DocumentAnalysis)
class DocumentAnalysisAdmin(admin.ModelAdmin):
    list_display = ['document', 'created_at']
    search_fields = ['document__file', 'document__uploaded_by__email']
    readonly_fields = ['document', 'created_at']


@admin.register(ChatConversation)
class ChatConversationAdmin(admin.ModelAdmin):
    list_display = ['id', 'document', 'user', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['question', 'document__file', 'user__email']
    readonly_fields = ['id', 'created_at', 'updated_at']

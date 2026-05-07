from django.urls import path
from . import views

urlpatterns = [
    path('', views.list_documents, name='list_documents'),
    path('upload/', views.upload_document, name='upload_document'),
    path('<int:pk>/', views.get_document, name='get_document'),
    path('<int:pk>/status/', views.get_document_status, name='get_document_status'),
    path('<int:pk>/chat/<int:conversation_id>/status/', views.get_chat_conversation_status, name='get_chat_conversation_status'),
    path('<int:pk>/chat/<int:conversation_id>/', views.get_chat_conversation, name='get_chat_conversation'),
    path('<int:pk>/chat/list/', views.list_chat_conversations, name='list_chat_conversations'),
    path('<int:pk>/chat/', views.chat_with_document, name='chat_with_document'),
]
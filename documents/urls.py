from django.urls import path
from . import views

urlpatterns = [
    path('', views.list_documents, name='list_documents'),
    path('upload', views.upload_document, name='upload_document'),
    path('<int:pk>/', views.get_document, name='get_document'),
    path('<int:pk>/status/', views.get_document_status, name='get_document_status'),
]
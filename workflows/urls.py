from django.urls import path
from .views import WorkflowViewSet

# Manually define URLs to avoid router converter conflicts
urlpatterns = [
    path('', WorkflowViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='workflow-list'),
    path('<int:pk>/', WorkflowViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='workflow-detail'),
]

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Document
from .serializers import DocumentSerializer
from .tasks import process_document


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_document(request):
    """
    Upload a document for processing.
    
    POST /api/documents/upload
    Headers: Authorization: Bearer {token}
    Body: multipart/form-data with 'file' field
    Returns: {"id": 1, "status": "UPLOADED"}
    """
    serializer = DocumentSerializer(data=request.data)
    if serializer.is_valid():
        document = serializer.save(uploaded_by=request.user)
        # Trigger Celery task
        process_document.delay(document.id)
        return Response(
            {
                'id': document.id,
                'status': document.status,
                'message': 'Document uploaded successfully. Processing started.'
            },
            status=status.HTTP_201_CREATED
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_document(request, pk):
    """
    Get a specific document.
    
    GET /api/documents/{id}/
    Headers: Authorization: Bearer {token}
    Returns: Document object
    """
    try:
        document = Document.objects.get(pk=pk, uploaded_by=request.user)
        serializer = DocumentSerializer(document)
        return Response(serializer.data)
    except Document.DoesNotExist:
        return Response(
            {'error': 'Document not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_document_status(request, pk):
    """
    Get the processing status of a document.
    
    GET /api/documents/{id}/status/
    Headers: Authorization: Bearer {token}
    Returns: {"status": "PROCESSING"}
    """
    try:
        document = Document.objects.get(pk=pk, uploaded_by=request.user)
        return Response({'status': document.status})
    except Document.DoesNotExist:
        return Response(
            {'error': 'Document not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_documents(request):
    """
    List all documents uploaded by the current user.
    
    GET /api/documents/
    Headers: Authorization: Bearer {token}
    Returns: List of documents
    """
    docs = Document.objects.filter(uploaded_by=request.user).order_by('-created_at')
    serializer = DocumentSerializer(docs, many=True)
    return Response(serializer.data)

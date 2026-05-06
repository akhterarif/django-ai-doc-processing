from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Document, ChatConversation
from .serializers import DocumentSerializer, ChatConversationSerializer
from .tasks import process_document, process_chat_question
from ai.llm import ask_llm
from ai.chroma import query_document_chunks
import logging

logger = logging.getLogger(__name__)

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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def chat_with_document(request, pk):
    """
    Ask a question about a specific document.
    
    POST /api/documents/{id}/chat/
    Headers: Authorization: Bearer {token}
    Body: {"question": "What is the main topic?"}
    Returns: {"conversation_id": 1, "status": "PENDING", "message": "Question submitted for processing"}
    """
    try:
        # Verify document ownership
        document = Document.objects.get(pk=pk, uploaded_by=request.user)
        
        # Check document is completed processing
        if document.status != 'COMPLETED':
            return Response(
                {'error': f'Document processing status: {document.status}. Please wait for COMPLETED status.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get question from request
        question = request.data.get('question', '').strip()
        if not question:
            return Response(
                {'error': 'Question is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create chat conversation record
        conversation = ChatConversation.objects.create(
            document=document,
            user=request.user,
            question=question,
            status='PENDING'
        )
        
        # Trigger Celery task for background processing
        process_chat_question.delay(conversation.id)
        
        return Response({
            'conversation_id': conversation.id,
            'status': conversation.status,
            'message': 'Question submitted for processing. Check status to get the answer.',
            'question': question,
        }, status=status.HTTP_201_CREATED)
    
    except Document.DoesNotExist:
        return Response(
            {'error': 'Document not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error creating chat conversation for document {pk}: {e}")
        return Response(
            {'error': 'An error occurred while submitting your question'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_chat_conversation(request, pk, conversation_id):
    """
    Get a specific chat conversation.
    
    GET /api/documents/{id}/chat/{conversation_id}/
    Headers: Authorization: Bearer {token}
    Returns: Chat conversation with answer if completed
    """
    try:
        # Verify document ownership
        document = Document.objects.get(pk=pk, uploaded_by=request.user)
        logger.info(f"Retrieved conversation {conversation_id} for document {pk}")
        
        # Get conversation
        conversation = ChatConversation.objects.get(
            id=conversation_id,
            document=document,
            user=request.user
        )
        logger.info(f"Retrieved conversation {conversation.id} for document {pk} with status {conversation.status}")
        
        serializer = ChatConversationSerializer(conversation)
        return Response(serializer.data)
    
    except Document.DoesNotExist:
        return Response(
            {'error': 'Document not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except ChatConversation.DoesNotExist:
        return Response(
            {'error': 'Conversation not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_chat_conversation_status(request, pk, conversation_id):
    """
    Get the status of a chat conversation.
    
    GET /api/documents/{id}/chat/{conversation_id}/status/
    Headers: Authorization: Bearer {token}
    Returns: {"status": "PROCESSING"}
    """
    try:
        # Verify document ownership
        document = Document.objects.get(pk=pk, uploaded_by=request.user)
        
        # Get conversation
        conversation = ChatConversation.objects.get(
            id=conversation_id,
            document=document,
            user=request.user
        )
        
        return Response({'status': conversation.status})
    
    except Document.DoesNotExist:
        return Response(
            {'error': 'Document not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except ChatConversation.DoesNotExist:
        return Response(
            {'error': 'Conversation not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_chat_conversations(request, pk):
    """
    List all chat conversations for a document.
    
    GET /api/documents/{id}/chat/
    Headers: Authorization: Bearer {token}
    Returns: List of chat conversations
    """
    try:
        # Verify document ownership
        document = Document.objects.get(pk=pk, uploaded_by=request.user)
        
        # Get conversations
        conversations = ChatConversation.objects.filter(
            document=document,
            user=request.user
        ).order_by('-created_at')
        
        serializer = ChatConversationSerializer(conversations, many=True)
        return Response(serializer.data)
    
    except Document.DoesNotExist:
        return Response(
            {'error': 'Document not found'},
            status=status.HTTP_404_NOT_FOUND
        )

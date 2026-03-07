from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Document, DocumentAnalysis
from .serializers import DocumentSerializer, DocumentAnalysisSerializer
from .tasks import process_document

@api_view(['POST'])
def upload_document(request):
    serializer = DocumentSerializer(data=request.data)
    if serializer.is_valid():
        document = serializer.save()
        # Trigger Celery task
        process_document.delay(document.id)
        return Response({'id': document.id, 'status': document.status}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def get_document(request, pk):
    try:
        document = Document.objects.get(pk=pk)
        serializer = DocumentSerializer(document)
        data = serializer.data
        if document.status == 'completed':
            analysis = DocumentAnalysis.objects.get(document=document)
            analysis_serializer = DocumentAnalysisSerializer(analysis)
            data['analysis'] = analysis_serializer.data
        return Response(data)
    except Document.DoesNotExist:
        return Response({'error': 'Document not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
def get_document_status(request, pk):
    try:
        document = Document.objects.get(pk=pk)
        return Response({'status': document.status})
    except Document.DoesNotExist:
        return Response({'error': 'Document not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
def list_documents(request):
    docs = Document.objects.all().order_by('-created_at')
    serializer = DocumentSerializer(docs, many=True)
    data = serializer.data
    # attach analysis where available
    for item in data:
        if item['status'] == 'completed':
            try:
                analysis = DocumentAnalysis.objects.get(document_id=item['id'])
                a_ser = DocumentAnalysisSerializer(analysis)
                item['analysis'] = a_ser.data
            except DocumentAnalysis.DoesNotExist:
                item['analysis'] = None
    return Response(data)

# Scaffold Serializer

Generate a Django REST Framework serializer for a model or an AI response schema.

## Arguments
$ARGUMENTS — Model name or description of the data structure to serialize
(e.g., `DocumentChunk model`, `QA answer with source chunks`)

## Steps

1. **Read** `documents/models.py` to find the model if it exists.
2. **Read** `documents/serializers.py` to understand current patterns and avoid
   naming conflicts.

3. **Generate the serializer** following these rules:

   **For a Django model** — use `ModelSerializer`:
   ```python
   class YourModelSerializer(serializers.ModelSerializer):
       class Meta:
           model = YourModel
           fields = ['id', 'field_one', 'field_two', 'created_at']
           read_only_fields = ['id', 'created_at', 'updated_at', 'status']
   ```
   - Always list `fields` explicitly — never `fields = '__all__'`
   - Mark as `read_only`: `id`, `created_at`, `updated_at`, `status`, and any
     field populated by AI/Celery tasks (not set by the API caller)

   **For a non-model AI response** — use `Serializer`:
   ```python
   class QAAnswerSerializer(serializers.Serializer):
       answer = serializers.CharField()
       confidence = serializers.FloatField(min_value=0.0, max_value=1.0)
       source_chunk_ids = serializers.ListField(child=serializers.IntegerField())
       reasoning = serializers.CharField(allow_blank=True)
   ```

   **For nested relationships** — always use a separate serializer class:
   ```python
   class DocumentWithAnalysisSerializer(serializers.ModelSerializer):
       analysis = DocumentAnalysisSerializer(source='documentanalysis', read_only=True)

       class Meta:
           model = Document
           fields = ['id', 'file', 'status', 'created_at', 'analysis']
           read_only_fields = ['id', 'status', 'created_at']
   ```

4. **If a new endpoint is needed** for this serializer, also generate:
   - The view function stub (function-based `@api_view`)
   - The URL pattern to add to `documents/urls.py`

5. **Output** the complete serializer class (and view/URL if applicable), ready
   to paste into the appropriate file.

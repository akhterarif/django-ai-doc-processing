# Add AI Feature

Add a new AI-powered analysis capability to the document processing pipeline,
following production patterns: Pydantic validation, chunking, caching, retries,
and token-cost awareness.

## Arguments
$ARGUMENTS — Name and description of the AI feature
(e.g., "named entity extraction using GPT-4o structured outputs")

## Steps

1. **Read** `documents/tasks.py` to understand the current `process_document`
   pipeline and `summarize_with_ai` function.

2. **Read** `documents/models.py` to determine storage needs:
   - New field on `DocumentAnalysis` if it's a simple addition
   - New model (e.g., `DocumentEntity`, `DocumentEmbedding`) if it's a separate
     analytical concern with its own lifecycle

3. **Select the right AI provider and model**:

   | Use case | Provider | Model |
   |---|---|---|
   | Complex reasoning, structured output | OpenAI | `gpt-4o` |
   | Cost-efficient summaries, short docs | OpenAI | `gpt-3.5-turbo` |
   | Long-context analysis (>16k tokens) | Anthropic | `claude-3-5-sonnet-20241022` |
   | Semantic embeddings | OpenAI | `text-embedding-3-small` |
   | Semantic reranking | Cohere | `rerank-english-v3.0` |

4. **Implement with these production patterns**:
   - Define Pydantic schema in `documents/schemas.py` for the AI response
   - Use OpenAI JSON mode or function calling for structured extraction
   - Count tokens with `tiktoken` before calling — chunk if doc exceeds model limit
   - Cache results in Redis keyed by `sha256(document_text)` to avoid re-processing
   - Wrap AI calls with exponential backoff retry (already in task template)
   - Log `token_usage` (prompt + completion tokens) at INFO level for cost tracking

5. **Wire into pipeline**:
   - Add as a new step in `process_document`, OR
   - Create a separate Celery task chained with `process_document.si() | new_task.si()`
   - Update serializers to expose new fields in API response

6. **Write tests**:
   - Patch the AI client (`unittest.mock.patch`)
   - Provide a fixture response matching the Pydantic schema
   - Test success, failure, and chunked-document paths

7. **Output**:
   - New packages to add to `requirements.txt`
   - New env vars to add to `.env.example`
   - API response field changes
   - Estimated token cost per average document

## Token Budget Guidelines

| Model | Input cost | Output cost | Max context |
|---|---|---|---|
| gpt-4o | $2.50/1M tokens | $10/1M tokens | 128k |
| gpt-3.5-turbo | $0.50/1M tokens | $1.50/1M tokens | 16k |
| claude-3-5-sonnet | $3/1M tokens | $15/1M tokens | 200k |
| text-embedding-3-small | $0.02/1M tokens | — | 8k |

Always log and store token counts so cost can be attributed per document.

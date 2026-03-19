# AI & Backend Engineering Skills Demonstrated

This project is a portfolio artifact targeting **Senior / Staff AI Backend Engineering** roles.

---

## Currently Demonstrated

### Async Task Architecture
- Celery + Redis task queue for non-blocking AI document processing
- Document status state machine: `uploaded → processing → completed | failed`
- Webhook notification system (success + failure payloads) for external system integration
- Docker Compose multi-service orchestration: Django, Celery, PostgreSQL, Redis, Next.js

### REST API Design
- Django REST Framework with serializers and function-based views
- Multipart file upload handling
- Consistent status-poll pattern for long-running async tasks

### AI Integration
- OpenAI GPT-3.5-turbo for document summarization
- PDF text extraction pipeline with PyPDF2
- Token-aware truncation for context window management

### DevOps & Infrastructure
- Containerized development and deployment with Docker + Docker Compose
- Environment-based configuration management via `.env`
- PostgreSQL + Redis production service configuration with health checks
- Shared Docker image for web + Celery worker (command-differentiated services)

### Full-Stack
- Next.js frontend with Tailwind CSS
- CORS-enabled Django API consumed by Next.js pages
- Polling-based status updates from frontend

---

## Roadmap Skills (Planned Features)

### Structured AI Outputs — Feature 1
- `openai>=1.50` SDK migration from legacy `0.28`
- Pydantic v2 models for AI response validation and schema enforcement
- JSON mode / structured outputs to replace fragile string splitting

### Intelligent Text Chunking — Feature 2
- Token-accurate chunking with `tiktoken`
- Celery `chord()` for parallel chunk summarization (map-reduce pattern)
- Hierarchical reduction: chunk summaries → final synthesis

### Vector Embeddings + Semantic Search — Feature 3
- OpenAI `text-embedding-3-small` for document chunk embeddings
- `pgvector` PostgreSQL extension for cosine similarity search
- Semantic search endpoint — no dedicated vector DB dependency

### RAG-Powered Document Q&A — Feature 4
- Retrieval-Augmented Generation with source attribution per answer
- Chunk-level grounding to mitigate hallucination
- `DocumentQALog` model for evaluation data collection

### Multi-Model AI Architecture — Feature 5
- Provider abstraction layer (`BaseAIProvider`, `OpenAIProvider`, `AnthropicProvider`)
- Intelligent model routing by document length and task type
- Anthropic Claude 3.5 Sonnet for long-context (200k token) whole-document analysis
- GPT-4o for structured extraction; GPT-3.5-turbo for cost-efficient short summaries

### Streaming AI Responses — Feature 6
- Server-Sent Events (SSE) via Django `StreamingHttpResponse`
- OpenAI + Anthropic streaming API integration
- Real-time token delivery to Next.js `EventSource` client

### Agentic Document Analysis — Feature 7
- LangGraph `StateGraph` for multi-step autonomous document analysis
- ReAct-style tool selection: entity extraction, classification, compliance check, web search
- Full reasoning trace stored in `AgentAnalysis.reasoning_trace JSONField` for auditability

### Named Entity Extraction + Knowledge Graph — Feature 8
- GPT-4o structured outputs with Pydantic `EntityExtractionSchema`
- Normalized `Entity` + `EntityRelationship` relational schema
- Cross-document entity co-occurrence graph exported via `networkx`

### Production Observability — Feature 9
- OpenTelemetry distributed tracing: API request → Celery task → AI provider call
- Prometheus metrics: request latency, token usage, task queue depth, error rates
- `structlog` for structured JSON logging (replaces `logging.basicConfig`)
- Grafana dashboard with AI-specific panels (cost/document, model latency histograms)

### Production Resilience — Feature 10
- Content-hash-keyed Redis cache — re-uploading identical documents skips AI processing
- Redis-backed circuit breaker shared across Celery workers (CLOSED / OPEN / HALF_OPEN)
- Per-endpoint rate limiting with `django-ratelimit`
- Exponential backoff retries for all AI provider calls

---

## Implementation Sequence

```
Feature 1 (SDK + Pydantic)
    ├── Feature 2 (Chunking)
    │       └── Feature 3 (pgvector embeddings)
    │               └── Feature 4 (RAG Q&A)
    │               └── Feature 8 (Entity graph)
    ├── Feature 5 (Multi-model routing)
    │       ├── Feature 6 (Streaming SSE)
    │       └── Feature 7 (LangGraph agent)
    ├── Feature 9 (Observability)   ← can be layered on at any point
    └── Feature 10 (Resilience)     ← can be layered on at any point
```

**Recommended order**: `1 → 2 → 3 → 4 → 5 → 10 → 9 → 6 → 7 → 8`

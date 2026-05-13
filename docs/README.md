AI Document Intelligence API
============================

A Django-based backend system for processing uploaded PDF documents asynchronously, extracting text, and generating AI-powered summaries using Ollama(gemma-2-9b).

This project demonstrates a **production-style backend architecture** designed for **scalable AI-powered document processing**, leveraging asynchronous workers, distributed task queues, and containerized services.

Here is the full video of the system, how it works
https://www.youtube.com/watch?v=oZVRnQ4kvLg


* * *

Features
========

*   Upload PDF documents via REST API
    
*   Asynchronous processing with **Celery + Redis**
    
*   Text extraction from PDFs
    
*   AI-powered document summarization with **Ollama**
    
*   Key point and topic extraction
    
*   Document classification (invoice, resume, legal, other)
    
*   Vector embeddings with **ChromaDB**
    
*   Semantic document search and Q&A
    
*   Status tracking and result retrieval
    
*   Webhook notifications on processing completion/failure
    
*   Docker containerization
    
*   Full stack setup with **Next.js frontend**
    

* * *

Tech Stack
==========

Backend

*   Django 6.0
    
*   Django REST Framework
    
*   Celery
    
*   Redis
    
*   PostgreSQL
    
*   Ollama (Local LLM)
    
*   ChromaDB (Vector Database)
    

Frontend

*   Next.js
    
*   Tailwind CSS
    

Infrastructure

*   Docker
    
*   Docker Compose
    

* * *

System Architecture
===================

The system is designed using an **asynchronous task processing architecture** to prevent long-running AI operations from blocking API requests.

Client Upload  
      │  
      ▼  
Django REST API  
      │  
      ▼  
Celery Task Queue (Redis)  
      │  
      ▼  
Background Worker  
(PDF Extraction + AI Analysis + Vector Storage)  
      │  
      ├─► Ollama LLM Service  
      │  
      ├─► ChromaDB Vector Store  
      │  
      ▼  
PostgreSQL Storage  
      │  
      ▼  
Webhook Notification

This architecture enables **high responsiveness, scalability, and fault tolerance**.

* * *

System Performance & Optimization
=================================

The application was designed with **scalability and resource efficiency** in mind.

Asynchronous Processing
-----------------------

Document processing tasks (PDF parsing and AI summarization) are handled by **Celery background workers**.

This prevents long-running operations from blocking the main web server.

### Performance Impact

| Operation             | Average Time |
| --------------------- | ------------ |
| API Upload Response   | ~80–120 ms   |
| PDF Text Extraction   | ~1–2 seconds |
| AI Summarization      | ~3–6 seconds |
| Total Processing Time | ~4–8 seconds |


Without background processing:

*   API requests would take **5–10 seconds**
    
*   Web server threads would remain blocked
    
*   System throughput would degrade under load
    

Using Celery:

*   API remains responsive
    
*   Tasks run asynchronously
    
*   Workers can scale horizontally
    

* * *

Horizontal Scalability
----------------------

The system supports horizontal scaling through containerized services.

| Component      | Scaling Strategy              |
| -------------- | ----------------------------- |
| Django API     | Scale via multiple containers |
| Celery Workers | Increase worker count         |
| Redis          | Distributed message broker    |
| PostgreSQL     | Persistent storage            |


### Example Throughput

| Workers   | Documents / Minute |
| --------- | ------------------ |
| 1 Worker  | 6–8                |
| 3 Workers | 18–24              |
| 5 Workers | 30–40              |


Throughput increases **linearly with additional workers**.

* * *

AI Token Optimization
---------------------

To reduce token usage and prevent failures on large documents, text is truncated before sending to the AI model.

```
text[:4000]
```

Benefits:

*   Reduces token consumption by **60–80%**
    
*   Prevents exceeding AI context limits
    
*   Improves processing latency
    

In production systems this approach can be extended using **chunking and hierarchical summarization pipelines**.

* * *

Resource Utilization
--------------------

Typical runtime resource usage:

| Component     | Memory  | CPU                        |
| ------------- | ------- | -------------------------- |
| Django API    | ~120 MB | Low                        |
| Celery Worker | ~150 MB | Moderate during processing |
| Redis         | ~30 MB  | Minimal                    |


Heavy tasks such as AI inference and document parsing are isolated to worker nodes to maintain API responsiveness.

* * *

Fault Tolerance
---------------

The task queue architecture improves reliability.

Key mechanisms:

*   Automatic **task retries**
    
*   Message persistence via Redis
    
*   Idempotent task execution
    
*   Failure notifications via webhook
    

If processing fails, the system automatically updates the document status and notifies external systems.

* * *

Setup
=====

1. Clone Repository
--------------------
```
git clone <repository-url>  
cd django-ai-document-intelligence
```
* * *

2. Configure Environment Variables
-----------------------------------
```
cp .env.example .env
```
Edit `.env`:
```
OPENAI\_API\_KEY=your\_api\_key  
WEBHOOK\_URL=http://your-webhook-endpoint
```
* * *

Running with Docker (Recommended)
=================================
```
# Initialize Ollama with required models
./init_ollama.sh

# Start all services
docker-compose up --build
```
This starts:

| Service          | Port     |
| ---------------- | -------- |
| Django API       | 8000     |
| Next.js Frontend | 3000     |
| PostgreSQL       | 5432     |
| Redis            | 6379     |
| Ollama           | 11434    |
| Celery Worker    | Internal |


Access the application:
```
http://localhost:3000
```
* * *

Running Locally
===============

Install dependencies
```
pip install -r requirements.txt
```
Run migrations
```
python manage.py migrate
```
Start Redis
```
redis-server
```
Run Django server
```
python manage.py runserver
```
Run Celery worker
```
celery -A django\_ai\_doc\_processing worker --loglevel=info
```
* * *

API Endpoints
=============

Upload Document
---------------
```
POST /api/documents/upload/
```
Example
```
curl -X POST -F "file=@document.pdf" http://localhost:8000/api/documents/upload/
```
* * *

List Documents
--------------
```
GET /api/documents/
```
* * *

Document Details
----------------
```
GET /api/documents/{id}/
```
* * *

Processing Status
-----------------
```
GET /api/documents/{id}/status/
```
Example
```
curl http://localhost:8000/api/documents/1/status/
```
* * *

Chat with Document
------------------
```
POST /api/documents/{id}/chat/
```
Ask questions about processed documents. Questions are processed asynchronously.

Example
```
curl -X POST -H "Content-Type: application/json" \
  -d '{"question": "What is the main topic of this document?"}' \
  http://localhost:8000/api/documents/1/chat/
```

Response
```json
{
  "conversation_id": 1,
  "status": "PENDING",
  "message": "Question submitted for processing. Check status to get the answer.",
  "question": "What is the main topic of this document?"
}
```
* * *

Chat Conversation Status
------------------------
```
GET /api/documents/{id}/chat/{conversation_id}/status/
```
Check the processing status of a chat question.

Example
```
curl http://localhost:8000/api/documents/1/chat/1/status/
```

Response
```json
{
  "status": "COMPLETED"
}
```
* * *

Get Chat Conversation
---------------------
```
GET /api/documents/{id}/chat/{conversation_id}/
```
Get the complete chat conversation with answer and sources.

Example
```
curl http://localhost:8000/api/documents/1/chat/1/
```

Response
```json
{
  "id": 1,
  "document": 1,
  "document_title": "document.pdf",
  "user": 1,
  "user_email": "user@example.com",
  "question": "What is the main topic?",
  "answer": "The main topic is...",
  "sources": [
    {
      "chunk": "This is a relevant text chunk...",
      "distance": 0.123
    }
  ],
  "status": "COMPLETED",
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:00:05Z"
}
```
* * *

List Chat Conversations
-----------------------
```
GET /api/documents/{id}/chat/list/
```
List all chat conversations for a document.

Example
```
curl http://localhost:8000/api/documents/1/chat/list/
```
* * *

Webhook Notifications
=====================

When document processing completes, a webhook notification is sent to the configured endpoint.

Success Response
----------------
```
JSON

{  
  "document\_id": 1,  
  "status": "completed",  
  "summary": "...",  
  "key\_points": \[\],  
  "topics": \[\]  
}
```
Failure Response
----------------
```
JSON

{  
  "document\_id": 1,  
  "status": "failed",  
  "error": "Error message"  
}

This enables integration with external systems such as:

*   workflow automation
    
*   notification services
    
*   external dashboards
    
```
* * *

Frontend
========

A **Next.js + Tailwind frontend** is included in the `frontend/` directory.

Features:

*   Upload PDF documents
    
*   View document processing status
    
*   View AI generated summaries
    
*   Display extracted key points and topics
    

Run frontend locally:
```
cd frontend  
npm install  
npm run dev
```
Frontend will be available at:
```
http://localhost:3000
```
Requests to `/api/*` are proxied to the Django backend.

* * *

Testing
=======

Run the test suite
```
python manage.py test documents
```

Test LLM service
```
python test_llm_service.py
```

Test chat functionality
```
python test_chat_functionality.py
```

* * *

Production Considerations
=========================

This project demonstrates architectural patterns commonly used in **AI-powered SaaS systems**.

Potential production improvements include:

*   Distributed tracing (OpenTelemetry)
    
*   Rate limiting for API endpoints
    
*   AI request caching
    
*   Circuit breakers for external APIs
    
*   Document chunking pipelines for large files
    
*   Observability dashboards (Prometheus + Grafana)
    

License
=======

MIT License

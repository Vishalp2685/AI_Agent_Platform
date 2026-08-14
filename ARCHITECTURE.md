# AI Agent Platform Architecture

## 1. Overview

This project is a Python-based AI agent platform that combines:

- a FastAPI backend for chat and document processing,
- a retrieval-augmented generation (RAG) pipeline for grounding answers in uploaded documents,
- a PostgreSQL + pgvector database for persistence and semantic search,
- Redis for short-term chat session caching,
- and MCP-based tool execution so the agent can interact with external tools.

The platform is designed as a modular learning-oriented system for experimenting with agent behavior, LLM integration, memory, and tool use.

---

## 2. High-Level Architecture

The system can be viewed as five major layers:

1. Client layer
   - A lightweight frontend served from [frontend/](frontend/)
   - Used for basic interactions with the API and document upload experience

2. API layer
   - Built with FastAPI in [main.py](main.py)
   - Exposes endpoints for chat sessions, chat history, document upload, and tool inspection

3. Application services layer
   - Handles LLM orchestration, RAG retrieval, and MCP tool execution
   - Key modules live in [llms/](llms/), [rag/](rag/), and [mcps/](mcps/)

4. Data layer
   - PostgreSQL stores sessions, messages, documents, and vector embeddings
   - pgvector enables similarity search over document chunks
   - Redis caches chat session state temporarily

5. Storage and runtime layer
   - Uploaded PDF files are saved locally in [uploads/](uploads/)
   - Environment configuration is loaded from the project environment file

---

## 3. Core Components

### 3.1 FastAPI Application

The main application entry point is [main.py](main.py).

It provides the following responsibilities:

- starts the app lifecycle and verifies Redis and database connectivity,
- initializes the MCP filesystem tool server,
- exposes endpoints for:
  - creating chat sessions,
  - retrieving chat history,
  - generating AI responses,
  - uploading and indexing documents,
  - listing available tools.

### 3.2 Frontend

The frontend is a simple static web UI located in [frontend/](frontend/):

- [frontend/index.html](frontend/index.html)
- [frontend/app.js](frontend/app.js)
- [frontend/style.css](frontend/style.css)

It interacts with the FastAPI backend through HTTP requests and is currently lightweight and client-side.

---

## 4. Request Flow

### 4.1 Chat Flow

1. A client sends a chat request to the /chat/get_response endpoint.
2. The backend checks Redis for prior chat history for the session.
3. If cache is missing, it loads chat history from PostgreSQL.
4. The user message is embedded using the embedding model.
5. Relevant document chunks are retrieved from the vector database.
6. The LLM is called with the user message, retrieved context, and chat history.
7. The assistant response is saved to the database and cached in Redis.

### 4.2 Document Upload and RAG Flow

1. A PDF is uploaded via the /documents/upload/ endpoint.
2. The file is saved to the local uploads directory.
3. Metadata is saved to the database.
4. The PDF text is extracted.
5. The text is split into chunks.
6. Each chunk is embedded with a sentence transformer model.
7. The embeddings are stored in PostgreSQL using pgvector.
8. Later chat requests retrieve relevant chunks for answer grounding.

---

## 5. Data Architecture

### 5.1 Relational Database

The database layer is implemented in [database/database.py](database/database.py) and [database/models.py](database/models.py).

The schema includes:

- ChatSessions
  - stores chat session identifiers

- ChatMessages
  - stores messages exchanged in each session

- Documents
  - stores uploaded document metadata

- DocumentChunks
  - stores chunk text and vector embeddings for semantic search

### 5.2 Vector Search

The project uses pgvector for semantic similarity search.

Relevant code:
- [database/curd.py](database/curd.py)
- [rag/embeddings.py](rag/embeddings.py)
- [rag/chunker.py](rag/chunker.py)

This enables the system to retrieve chunks that are semantically relevant to the user query, rather than relying only on keyword matching.

### 5.3 Redis Cache

Redis is used for temporary caching of chat session state.

Its purpose is to:

- reduce database load for repeated chat history access,
- speed up session retrieval,
- keep recent chat state available in memory.

---

## 6. RAG Pipeline

The RAG pipeline is one of the core architectural ideas of the platform.

### 6.1 Document ingestion

- A document is uploaded through the API.
- The file is stored in [uploads/](uploads/).
- Metadata is written to the database.

### 6.2 Text extraction

PDF content is extracted using [rag/extractor.py](rag/extractor.py).

### 6.3 Chunking

Text is split into manageable chunks using [rag/chunker.py](rag/chunker.py).

### 6.4 Embedding generation

Each chunk is converted into a vector using a sentence transformer model in [rag/embeddings.py](rag/embeddings.py).

### 6.5 Retrieval

During chat, the user message is embedded and compared against stored embeddings to fetch the most relevant chunks.

That retrieved context is fed into the LLM, allowing the assistant to answer based on uploaded documents rather than only the model’s pretraining.

---

## 7. LLM Layer

The LLM integration is implemented in [llms/gemini.py](llms/gemini.py).

Responsibilities:

- construct the prompt with retrieved document context and chat history,
- call the Gemini model,
- optionally invoke MCP tools when the model requests them,
- persist the model response into the database.

The system uses a structured prompt that includes:

- document context,
- the current user message,
- prior conversation history.

---

## 8. MCP and Tool Execution

The platform includes a Model Context Protocol (MCP) integration layer in [mcps/manager.py](mcps/manager.py).

### 8.1 Role of MCP

MCP allows the agent to call tools exposed by external servers.

In the current implementation, the platform initializes a filesystem MCP server and registers tools from it.

### 8.2 Tool flow

1. The model determines that a tool should be called.
2. The tool request is validated against its declared schema.
3. The MCP manager routes the tool call to the relevant session.
4. The tool response is sent back to the LLM.
5. The model can continue reasoning and produce a final response.

This makes the platform more agent-like, because the model is not just generating text; it can also act through tools.

---

## 9. Runtime Dependencies

The application depends on:

- FastAPI for API endpoints,
- SQLAlchemy for ORM-based database access,
- PostgreSQL for relational storage,
- pgvector for vector similarity search,
- Redis for caching,
- sentence-transformers for embeddings,
- Google Gemini for language model responses,
- MCP client libraries for tool execution.

---

## 10. Deployment and Environment Model

The project is designed to run locally with environment configuration such as:

- database connection settings,
- Redis host/port configuration,
- Gemini API key,
- other LLM-related credentials.

At startup, the application verifies that:

- Redis is reachable,
- the database is reachable,
- and MCP initialization succeeds.

If any of these checks fail, the service exits early.

---

## 11. Strengths of the Current Architecture

- Modular separation between API, RAG, LLM, tools, and persistence
- Clear support for document-grounded chat
- Vector search allows semantic retrieval instead of simple keyword search
- MCP integration adds tool-use capability to the agent
- The design is extensible for adding more agents, tools, and providers

---

## 12. Current Limitations

- The frontend is still minimal and mainly acts as a prototype interface
- The system currently focuses on a single MCP tool server and a single LLM provider
- The architecture is learning-oriented and may evolve as more production concerns are introduced
- File handling is local rather than distributed or cloud-based

---

## 13. Summary

This application is best understood as a modular AI agent platform with four core capabilities:

1. chat and session management,
2. document ingestion and indexing,
3. retrieval-augmented generation,
4. tool-enabled LLM reasoning through MCP.

In short, the architecture combines a web API, a vector database, an LLM, and tool execution into a single experimental agent platform.

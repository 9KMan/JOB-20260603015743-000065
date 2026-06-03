# Support AI Bot

A RAG-powered support bot that ingests a knowledge base and historical support tickets, then answers customer/internal queries grounded in that content.

## Features

- **RAG-style Retrieval**: Uses embeddings to find relevant context from knowledge base and support tickets
- **Chat Interface**: Real-time chat with source citations
- **Data Pipeline**: ETL pipeline for processing and indexing documents
- **Multi-source Search**: Searches both knowledge base articles and support ticket history
- **Flexible Vector Store**: Supports pgvector (local), Pinecone, or Weaviate
- **Modern Stack**: FastAPI + React + PostgreSQL

## Tech Stack

- **Backend**: Python, FastAPI, SQLAlchemy, PostgreSQL
- **Frontend**: React, TypeScript
- **AI/Embeddings**: OpenAI (ada-002), Anthropic (Claude)
- **Vector Storage**: pgvector, Pinecone, or Weaviate
- **Authentication**: JWT (HS256), bcrypt

## Project Structure

```
.
├── api/                    # FastAPI routes and schemas
├── models/                 # SQLAlchemy database models
├── services/               # Business logic (auth, chat, RAG)
├── embeddings/             # Embedding service
├── vector_store/           # Vector store implementations
├── data_pipeline/          # ETL pipeline for indexing
├── core/                   # Configuration and database
├── workers/                # Background jobs
├── migrations/             # Database migrations
├── tests/                  # Unit tests
├── frontend/                # React application
├── main.py                 # FastAPI application entry point
├── requirements.txt        # Python dependencies
└── docker-compose.yml      # Local development setup
```

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose (for local development)
- OpenAI API key (or configure another LLM)

### 1. Clone and Configure

```bash
# Clone the repository
git clone https://github.com/9KMan/JOB-20260603015743-000065.git
cd JOB-20260603015743-000065

# Copy environment template
cp .env.example .env

# Edit .env with your settings
# Add your OPENAI_API_KEY
```

### 2. Using Docker Compose (Recommended)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

The API will be available at http://localhost:8080
The frontend will be available at http://localhost:3000

### 3. Manual Setup

#### Backend

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Set up database
# Ensure PostgreSQL is running and accessible via DATABASE_URL

# Run the API
uvicorn main:app --reload --host 0.0.0.0 --port 8080
```

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register new user |
| POST | `/api/v1/auth/login` | Login and get JWT token |
| POST | `/api/v1/auth/login/json` | Login with JSON body |
| GET | `/api/v1/auth/me` | Get current user info |
| POST | `/api/v1/auth/logout` | Logout |

### Chat

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/chat/message` | Send a chat message |
| GET | `/api/v1/chat/history/{session_id}` | Get conversation history |
| DELETE | `/api/v1/chat/history/{session_id}` | Clear conversation history |

### Knowledge Base

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/knowledge-base/items` | Create KB item |
| GET | `/api/v1/knowledge-base/items` | List KB items |
| GET | `/api/v1/knowledge-base/items/{id}` | Get KB item |
| PUT | `/api/v1/knowledge-base/items/{id}` | Update KB item |
| DELETE | `/api/v1/knowledge-base/items/{id}` | Archive KB item |

### Support Tickets

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/tickets/` | Create ticket |
| GET | `/api/v1/tickets/` | List tickets |
| GET | `/api/v1/tickets/{id}` | Get ticket |
| GET | `/api/v1/tickets/by-number/{number}` | Get ticket by number |
| PUT | `/api/v1/tickets/{id}/status` | Update ticket status |

### Indexing

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/index/full` | Start full indexing job |
| GET | `/api/v1/index/jobs` | List index jobs |
| GET | `/api/v1/index/jobs/{id}` | Get job status |

## Usage Example

### Register and Login

```bash
# Register
curl -X POST http://localhost:8080/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","username":"user","password":"password123"}'

# Login
curl -X POST http://localhost:8080/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=password123"
```

### Chat

```bash
# Send message
curl -X POST http://localhost:8080/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"query":"How do I reset my password?","session_id":"test-session-1"}'
```

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `ANTHROPIC_API_KEY` | Anthropic API key (optional) | Optional |
| `DATABASE_URL` | PostgreSQL connection string | postgresql://... |
| `SECRET_KEY` | JWT secret key | Required |
| `USE_PGVECTOR` | Use pgvector instead of cloud | true |
| `PINECONE_API_KEY` | Pinecone API key | Optional |
| `WEAVIATE_URL` | Weaviate URL | Optional |

## Data Model

- **User**: Application users with JWT auth
- **KnowledgeBaseItem**: Articles/documents for RAG
- **SupportTicket**: Historical support tickets
- **TicketMessage**: Messages within tickets
- **DocumentChunk**: Chunked+embedded document pieces
- **Conversation**: Chat sessions
- **ConversationMessage**: Chat messages with RAG sources
- **IndexJob**: Background indexing job tracking

## Development

### Running Tests

```bash
# Run unit tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html
```

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "Add user table"

# Apply migrations
alembic upgrade head
```

## Architecture

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   Client    │──────│  FastAPI    │──────│ PostgreSQL  │
│   (React)   │      │   Backend   │      │  + pgvector │
└─────────────┘      └──────┬──────┘      └─────────────┘
                            │
                     ┌─────▼─────┐
                     │  Vector    │
                     │   Store    │
                     │ (pgvector) │
                     └───────────┘
                            │
                     ┌─────▼─────┐
                     │  Embedding │
                     │  Service   │
                     │ (OpenAI)   │
                     └───────────┘
```

## License

MIT License

## Author

Principal Data Platform Architect | AI-Augmented Engineering Factory
Bangkok, Thailand (GMT+7)

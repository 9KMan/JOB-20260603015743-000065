# Support AI Bot — RAG Knowledge Base + Ticket Ingestion

**Client:** AI Support Bot Client
**Tier:** LARGE | **Budget:** $5,000 fixed-price, 6-8 week MVP

---

## 🎯 Business Problem Solved

Customer support teams drown in repetitive tickets, but the answers are scattered across KB articles, past ticket threads, and tribal knowledge. This bot ingests a company's knowledge base and years of historical support tickets, then answers queries grounded in real evidence — citing sources to reduce hallucination.

**Pain:** Support teams handle 60-80% repetitive queries manually. Existing solutions either: (a) require hand-crafting every Q&A pair, (b) hallucinate without grounding, or (c) can't leverage the company's own historical ticket data.

**Solution delivered:** Production RAG pipeline that:
1. **Ingests** KB articles (HTML/PDF/Markdown) and historical tickets (Zendesk/Freshdesk/Intercom exports)
2. **Cleans & chunks** content (semantic splitting, metadata preservation)
3. **Embeds & indexes** into vector DB (Pinecone/Weaviate/pgvector)
4. **Retrieves** top-k relevant chunks per query (hybrid: vector + BM25)
5. **Generates** grounded answer with citations via LLM (OpenAI/Anthropic)
6. **Chat UI** — embeddable React widget for customer or internal use

**Key differentiators:** Hybrid retrieval (vector + keyword), explicit source citations, prompt-engineering for grounding, fastapi backend + React widget, evaluation harness to prevent regression.

---

## Quick Start

```bash
# Backend
cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend widget
cd frontend && npm install && npm run dev

# Ingest tickets + KB
python -m ingestion.ingest_kb ./data/kb/
python -m ingestion.ingest_tickets ./data/tickets.csv

# Test
pytest tests/
```

## Features

- **RAG-style Retrieval**: Embeddings find relevant context from knowledge base and tickets
- **Chat Interface**: Real-time chat with source citations
- **Data Pipeline**: ETL for processing and indexing documents
- **Multi-source Search**: Searches both KB articles and ticket history
- **Hybrid Search**: Combines vector similarity with BM25 keyword search
- **Citation Engine**: Every answer includes source IDs, chunk text, and confidence scores
- **Evaluation Harness**: Regression tests against labeled Q&A dataset

## Tech Stack

`python` · `openai` · `anthropic` · `pinecone` · `weaviate` · `pgvector` · `fastapi` · `react` · `embeddings` · `rag` · `chatbot` · `data-pipeline` · `etl`

## Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ KB Articles  │────▶│   Ingester   │────▶│   Chunker    │
│ (HTML/PDF)   │     │  (cleaning)  │     │ (semantic)   │
└──────────────┘     └──────────────┘     └──────┬───────┘
                                                 │
┌──────────────┐     ┌──────────────┐     ┌──────▼───────┐
│  Tickets     │────▶│  CSV/JSON    │────▶│  Embedder    │
│ (Zendesk/etc)│     │  parser      │     │  (OpenAI)    │
└──────────────┘     └──────────────┘     └──────┬───────┘
                                                 │
                                         ┌───────▼──────┐
                                         │ Vector DB    │
                                         │ (Pinecone/   │
                                         │  Weaviate/   │
                                         │  pgvector)   │
                                         └───────┬──────┘
                                                 │
┌──────────────┐     ┌──────────────┐     ┌───────▼──────┐
│   React      │────▶│   FastAPI    │────▶│  Retrieval   │
│  ChatWidget  │     │   /chat      │     │  (hybrid)    │
└──────────────┘     └──────────────┘     └───────┬──────┘
                                                 │
                                         ┌───────▼──────┐
                                         │  LLM with    │
                                         │  citations   │
                                         └───────┬──────┘
                                                 │
                                         ┌───────▼──────┐
                                         │  Answer +    │
                                         │  Sources     │
                                         └──────────────┘
```

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── main.py             ← FastAPI app
│   │   ├── retrieval.py        ← hybrid search (vector + BM25)
│   │   ├── generator.py        ← LLM with citations
│   │   └── models.py           ← Pydantic schemas
│   ├── ingestion/
│   │   ├── ingest_kb.py        ← KB articles
│   │   ├── ingest_tickets.py   ← historical tickets
│   │   ├── chunker.py          ← semantic chunking
│   │   └── embedder.py         ← OpenAI embeddings
│   └── tests/
│       ├── test_retrieval.py
│       ├── test_generator.py
│       └── eval_harness.py     ← regression tests
├── frontend/
│   ├── src/
│   │   ├── ChatWidget.tsx      ← embeddable React widget
│   │   ├── api.ts              ← backend client
│   │   └── citations.tsx       ← source display
│   └── package.json
└── data/
    ├── kb/                     ← input: KB articles
    └── tickets.csv             ← input: historical tickets
```

## Citations & Grounding

Every answer includes structured citations:
- `source_id`: pointer to original doc/ticket
- `chunk_text`: exact span used
- `confidence`: similarity score
- `relevance_rank`: hybrid-search rank

LLM prompt is engineered to: (1) refuse if no relevant context, (2) cite specific sources, (3) never invent IDs/URLs.

## Evaluation

`tests/eval_harness.py` runs the bot against a labeled set of (question, expected_topic, expected_source) tuples. Reports:
- Retrieval recall@k
- Citation accuracy
- Hallucination rate (manually labeled)
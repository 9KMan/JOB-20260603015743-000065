"""RAG service for retrieval-augmented generation."""
from typing import Optional
import openai
from core.config import settings
from data_pipeline.pipeline import retrieve_context


def build_rag_prompt(query: str, context_docs: list[dict]) -> str:
    """Build a prompt with retrieved context."""
    if not context_docs:
        return f"Answer the following question based on your general knowledge:\n\n{query}"

    context_parts = []
    for i, doc in enumerate(context_docs, 1):
        source = doc.get("metadata", {}).get("source", "unknown")
        title = doc.get("metadata", {}).get("title", doc.get("metadata", {}).get("ticket_number", ""))
        content = doc.get("metadata", {}).get("content", doc.get("metadata", {}).get("subject", ""))
        context_parts.append(f"[Source {i}] ({source}) {title}\n{content}")

    context_text = "\n\n".join(context_parts)

    prompt = f"""You are a helpful support bot. Answer the user's question based ONLY on the provided context.
If the context doesn't contain enough information to fully answer, say so.

CONTEXT:
{context_text}

QUESTION: {query}

ANSWER (be helpful and concise):"""
    return prompt


def generate_rag_response(
    query: str,
    top_k: int = 5,
    source_filter: Optional[str] = None,
    use_anthropic: bool = False
) -> dict:
    """Generate a RAG-based response to a query."""
    # Retrieve relevant context
    context_docs = retrieve_context(query, top_k=top_k, source_filter=source_filter)

    # Build prompt
    prompt = build_rag_prompt(query, context_docs)

    # Generate response
    if use_anthropic and settings.ANTHROPIC_API_KEY:
        import anthropic
        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        answer = response.content[0].text
        model_used = "anthropic-claude"
    else:
        openai.api_key = settings.OPENAI_API_KEY
        response = openai.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful support bot assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1024
        )
        answer = response.choices[0].message.content
        model_used = settings.OPENAI_MODEL

    return {
        "answer": answer,
        "sources": context_docs,
        "model_used": model_used,
        "tokens_used": response.usage.total_tokens if hasattr(response, "usage") else None
    }


def generate_response_stream(
    query: str,
    top_k: int = 5,
    source_filter: Optional[str] = None,
    use_anthropic: bool = False
):
    """Stream a RAG-based response (generator)."""
    context_docs = retrieve_context(query, top_k=top_k, source_filter=source_filter)
    prompt = build_rag_prompt(query, context_docs)

    if use_anthropic and settings.ANTHROPIC_API_KEY:
        import anthropic
        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        with client.messages.stream(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        ) as stream:
            for text in stream.text_stream:
                yield text
    else:
        openai.api_key = settings.OPENAI_API_KEY
        response = openai.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful support bot assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1024,
            stream=True
        )
        for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
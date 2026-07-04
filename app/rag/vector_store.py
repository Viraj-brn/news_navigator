from fastembed import TextEmbedding
from app.db.supabase_client import supabase

# Load the lightweight ONNX embedding model (uses <100MB RAM instead of 500MB+ for PyTorch)
_model = TextEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")


def create_knowledge_base(topic: str, chunks: list[dict]) -> None:
    """
    Generates embeddings for the given text chunks and upserts them
    into the Supabase `article_embeddings` table.
    """
    topic_lower = topic.strip().lower()

    # 1. Delete any existing embeddings for this topic to avoid duplicates
    supabase.table("article_embeddings").delete().eq("topic", topic_lower).execute()

    # 2. Prepare the texts for batch embedding
    texts = [chunk["text"] for chunk in chunks]
    
    # fastembed returns a generator of numpy arrays. Convert them to lists for JSON serialization.
    embeddings = [e.tolist() for e in _model.embed(texts)]

    # 3. Build rows for insertion
    rows = []
    for chunk, embedding in zip(chunks, embeddings):
        rows.append({
            "topic": topic_lower,
            "content": chunk["text"],
            "source_title": chunk["metadata"].get("source_title", ""),
            "source_link": chunk["metadata"].get("source_link", ""),
            "pub_date": chunk["metadata"].get("pub_date", ""),
            "embedding": embedding,
        })

    # 4. Insert in batches of 50 to avoid payload limits
    batch_size = 50
    for i in range(0, len(rows), batch_size):
        batch = rows[i : i + batch_size]
        supabase.table("article_embeddings").insert(batch).execute()

    print(f"[OK] Stored {len(rows)} chunks for topic '{topic_lower}' in Supabase.")


def retrieve_relevant_context(topic: str, query: str, top_k: int = 4) -> str:
    """
    Embeds the user query and calls the Supabase RPC function `match_documents`
    to find the most semantically similar article chunks.
    """
    topic_lower = topic.strip().lower()

    # 1. Embed the query (returns generator of 1 element)
    query_embedding = list(_model.embed([query]))[0].tolist()

    # 2. Call the Supabase RPC function
    try:
        result = supabase.rpc("match_documents", {
            "query_embedding": query_embedding,
            "match_topic": topic_lower,
            "match_threshold": 0.3,
            "match_count": top_k,
        }).execute()
    except Exception as e:
        print(f"[Warning] Supabase RPC error: {e}")
        return "No knowledge base found for this topic."

    # 3. Format the results for the LLM
    if not result.data:
        return "No relevant context found for this query in the knowledge base."

    context_blocks = []
    for row in result.data:
        block = f"Source: {row['source_title']}\nSnippet: {row['content']}"
        context_blocks.append(block)

    return "\n\n---\n\n".join(context_blocks)
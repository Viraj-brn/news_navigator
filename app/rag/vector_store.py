import chromadb
from chromadb.utils import embedding_functions

# Initialize an in-memory Chroma client (wipes when server restarts)
# For production, you'd use chromadb.PersistentClient(path="./data/embeddings")
chroma_client = chromadb.Client()

# Use a lightweight, fast local embedding model
sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

def create_knowledge_base(topic: str, chunks: list[dict]) -> chromadb.Collection:
    """
    Creates a new vector collection for the specific topic and adds the text chunks.
    """
    # Clean topic string to make a valid collection name (no spaces)
    collection_name = get_safe_collection_name(topic)
    
    # Get or create the collection
    collection = chroma_client.get_or_create_collection(
        name=collection_name,
        embedding_function=sentence_transformer_ef
    )
    
    # Extract lists for ChromaDB
    ids = [chunk["id"] for chunk in chunks]
    documents = [chunk["text"] for chunk in chunks]
    metadatas = [chunk["metadata"] for chunk in chunks]
    
    # Upsert data into the topological space
    collection.upsert(
        ids=ids,
        documents=documents,
        metadatas=metadatas
    )
    
    return collection

def retrieve_relevant_context(topic: str, query: str, top_k: int = 3) -> str:
    """
    Embeds the user query, finds the nearest neighbors in the vector space,
    and returns a formatted string of the most relevant chunks.
    """
    collection_name = get_safe_collection_name(topic)
    
    try:
        collection = chroma_client.get_collection(
            name=collection_name,
            embedding_function=sentence_transformer_ef
        )
    except ValueError:
        return "No knowledge base found for this topic."

    # Query the vector space
    results = collection.query(
        query_texts=[query],
        n_results=top_k
    )
    
    # Format the results into a single context string for the LLM
    context_blocks = []
    if results['documents'] and len(results['documents'][0]) > 0:
        for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
            block = f"Source: {meta['source_title']}\nSnippet: {doc}"
            context_blocks.append(block)
            
    return "\n\n---\n\n".join(context_blocks)

import re

def get_safe_collection_name(topic: str) -> str:
    """Generates a ChromaDB-safe collection name."""
    # Replace any non-alphanumeric character with an underscore
    safe_name = re.sub(r'[^a-zA-Z0-9]+', '_', topic)
    # Strip leading/trailing underscores and convert to lowercase
    safe_name = safe_name.strip('_').lower()
    
    # ChromaDB requires names to be between 3 and 63 characters
    if len(safe_name) < 3:
        safe_name = safe_name.ljust(3, 'a') # Pad with 'a' if too short
    
    return safe_name[:63] # Truncate if too long

# Then, in your functions, replace the old collection_name logic with:
# collection_name = get_safe_collection_name(topic)
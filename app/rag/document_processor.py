from langchain_text_splitters import RecursiveCharacterTextSplitter

def process_articles_into_chunks(articles: list[dict]) -> list[dict]:
    """
    Splits full articles into smaller, overlapping chunks for precise vector embedding.
    """
    # We use a 500 character chunk size with a 50 character overlap
    # to ensure sentences aren't cut completely in half.
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        length_function=len,
    )

    chunks = []
    
    for article_idx, article in enumerate(articles):
        # Combine title and description/body for context
        full_text = f"{article['title']}\n\n{article['description']}"
        
        # Split the text
        split_texts = text_splitter.split_text(full_text)
        
        for chunk_idx, text in enumerate(split_texts):
            chunks.append({
                "id": f"doc_{article_idx}_chunk_{chunk_idx}",
                "text": text,
                "metadata": {
                    "source_title": article['title'],
                    "source_link": article['link'],
                    "article_index": article_idx
                }
            })
            
    return chunks
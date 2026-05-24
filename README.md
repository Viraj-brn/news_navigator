# 📰 News Navigator

![News Navigator](https://img.shields.io/badge/Status-Live-success) ![Python](https://img.shields.io/badge/Python-3.10+-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white) ![Supabase](https://img.shields.io/badge/Supabase-pgvector-3ECF8E?logo=supabase&logoColor=white) ![Groq](https://img.shields.io/badge/Groq-Llama%203.3-f472b6)

**Live Demo:** [https://news-navigator-hro3.onrender.com/](https://news-navigator-hro3.onrender.com/)

News Navigator is a powerful, AI-driven intelligence platform that dynamically scrapes, synthesizes, and evaluates the latest news using Domain-Driven Design principles. Built with a high-performance stack, it delivers real-time briefings and features an automated Sentinel to monitor specific events.

## ✨ Features

- **Automated Intelligence Briefings**: Type any topic, and the system dynamically scrapes the latest RSS feeds to build a comprehensive, formatted executive briefing.
- **Interactive Follow-up Assistant**: Chat directly with the briefing using a LangGraph ReAct agent. It queries the local knowledge base to answer highly specific follow-up questions.
- **News Sentinel (Automated Monitoring)**: Define custom "Trigger Conditions" (e.g., *Tesla announces a new gigafactory*). The Sentinel will evaluate daily headlines using LLM logic and log an alert the moment a matching event occurs in the real world.
- **Serverless RAG Architecture**: Complete vector similarity search implemented via Supabase `pgvector` and lightweight `fastembed` ONNX models.

## 🛠 Tech Stack

- **Backend**: FastAPI (Python)
- **AI Orchestration**: LangGraph & LangChain
- **LLM**: Meta Llama-3.3-70b-versatile (via Groq for lightning-fast inference)
- **Vector Database**: PostgreSQL with `pgvector` (Supabase)
- **Embeddings**: `fastembed` (`all-MiniLM-L6-v2`) for ultra-low memory footprint
- **Frontend**: Vanilla HTML / CSS / JS with a premium dark-mode, glassmorphism UI

## 🚀 Running Locally

### Prerequisites
1. Python 3.10+
2. A free [Groq](https://console.groq.com/) API Key
3. A free [Supabase](https://supabase.com/) Project

### 1. Supabase Setup
Enable the vector extension and create the required tables by running this SQL snippet in your Supabase SQL Editor:
```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE article_embeddings (
    id BIGSERIAL PRIMARY KEY,
    topic TEXT NOT NULL,
    content TEXT NOT NULL,
    source_title TEXT,
    source_link TEXT,
    pub_date TEXT,
    embedding vector(384)
);

CREATE TABLE user_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    keyword TEXT NOT NULL,
    trigger_condition TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- Cosine similarity match function
CREATE OR REPLACE FUNCTION match_documents (
  query_embedding vector(384),
  match_threshold float,
  match_count int,
  p_topic text
)
RETURNS TABLE (
  id bigint,
  content text,
  source_title text,
  source_link text,
  pub_date text,
  similarity float
)
LANGUAGE sql STABLE
AS $$
  SELECT
    article_embeddings.id,
    article_embeddings.content,
    article_embeddings.source_title,
    article_embeddings.source_link,
    article_embeddings.pub_date,
    1 - (article_embeddings.embedding <=> query_embedding) AS similarity
  FROM article_embeddings
  WHERE article_embeddings.topic = p_topic
    AND 1 - (article_embeddings.embedding <=> query_embedding) > match_threshold
  ORDER BY article_embeddings.embedding <=> query_embedding
  LIMIT match_count;
$$;
```

### 2. Environment Variables
Create a `.env` file in the root directory:
```env
GROQ_API_KEY="your-groq-key"
SUPABASE_URL="your-supabase-url"
SUPABASE_KEY="your-supabase-anon-key"
```

### 3. Install & Run
```bash
# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn app.main:app --reload
```
Navigate to `http://localhost:8000` to start using the app.

## 📡 Triggering the Sentinel
Because the app is optimized for free hosting (which sleeps during inactivity), the background cron job has been converted into a triggerable HTTP endpoint.

To execute a daily check of all your active alerts, simply send a POST request to:
`POST /api/sentinel/run`

*Tip: Use a free service like [cron-job.org](https://cron-job.org/) to hit this endpoint once a day automatically.*

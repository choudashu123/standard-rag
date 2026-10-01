# Standard RAG — Project Details & Documentation

## 1. Project Overview
**Standard RAG** is a streamlined, production-ready Retrieval-Augmented Generation (RAG) platform designed to convert documents (PDF, TXT) into a queryable knowledge base. Combining modern LLMs with local semantic search, the system delivers grounded, factual answers to user questions while eliminating hallucinations.

---

## 2. System Architecture

The application is structured into two core layers:

```
┌─────────────────────────────────────────────────────────┐
│              Frontend (React 19 + Vite)                 │
│   • Dark Glassmorphism UI (Framer Motion + Lucide)      │
│   • Document Upload (PDF / TXT) & Instant Q&A Chat      │
│   • Knowledge Base Clear & Status Monitoring            │
└───────────────────────────▲─────────────────────────────┘
                            │ HTTP / JSON (REST)
┌───────────────────────────▼─────────────────────────────┐
│                 Backend (FastAPI - backend/app.py)          │
│   • Document Loader & Character/Recursive Splitter      │
│   • Google Gemini Embeddings (models/gemini-embedding)  │
│   • ChromaDB Persistent Vector Store                    │
│   • Google Gemini 2.5 Flash Synthesis Chain             │
│   • Automatic Multi-Key Rate-Limit Rotation             │
└─────────────────────────────────────────────────────────┘
```

- **Frontend (Presentation Layer):** React + Vite single-page application styled with a responsive dark glassmorphism theme and smooth animations.
- **Backend (Orchestration Layer):** A unified FastAPI server ([backend/app.py](file:///Users/ashutoshchoudhary/pro/standard-rag/backend/app.py)) managing document ingestion, chunking, indexing, and context-grounded retrieval.
- **Vector Intelligence:** **ChromaDB** persists vector indices locally under `chroma_db/`.
- **LLM & Embeddings:** Powered by **Google Gemini 2.5 Flash** for synthesis and **Google Generative AI Embeddings** (`gemini-embedding-001`).

---

## 3. Technology Stack

| Component | Technology | Rationale |
| :--- | :--- | :--- |
| **Backend Framework** | FastAPI (Python 3.9+) | Async performance, auto OpenAPI/Swagger docs, light footprint |
| **LLM Synthesis** | Google Gemini 2.5 Flash | Fast (<2s response time), cost-efficient, long context window |
| **Embeddings** | Google Generative AI Embeddings | Consistent semantic alignment with Gemini LLM |
| **Vector Store** | ChromaDB | Local, lightweight, persistent vector storage |
| **Orchestration** | LangChain Core / Community | Standard document loaders, text splitters, retrieval chains |
| **Frontend UI** | React 19 + Vite + Framer Motion | Modern, zero-latency UI with smooth micro-interactions |
| **Icons** | Lucide React | Lightweight vector iconography |

---

## 4. The Standard RAG Pipeline

```
[ Documents (PDF / TXT) ]
         │
         ▼
[ Recursive Chunking (1,000 chars, 200 overlap) ]
         │
         ▼
[ Google Gemini Embedding Generation ]
         │
         ▼
[ ChromaDB Persistent Vector Index ]
         │
         ▼ (When query received)
[ Semantic Cosine Retrieval (Top-3 Chunks) ]
         │
         ▼
[ Grounded Prompt + Gemini 2.5 Flash Synthesis ]
         │
         ▼
[ Concise Answer to User ]
```

### A. Document Ingestion
Supports `.pdf` (via `PyPDFLoader`) and `.txt` (via `TextLoader`). Uploaded files are safely stored in `data/uploads/`.

### B. Recursive Chunking
Text is segmented using LangChain's `RecursiveCharacterTextSplitter`:
- **Chunk Size:** 1,000 characters
- **Chunk Overlap:** 200 characters (20%)
- **Split Hierarchy:** `\n\n` (paragraphs) → `\n` (sentences) → `" "` (words) to preserve structural context.

### C. Vector Indexing & Semantic Search
Chunks are converted into high-dimensional vector representations and persisted to disk in `chroma_db/`. When a user submits a query:
1. The question is converted to an embedding vector.
2. A cosine similarity search in ChromaDB retrieves the **top 3** most relevant passages.

### D. Grounded Synthesis
Retrieved context is injected into a strict system prompt instructing Gemini to answer **only** from the retrieved excerpts within three concise sentences.

---

## 5. Alternative Chunking Strategies Reference

For future optimization or specialized document sets, the following chunking strategies can be utilized:

### 1. Fixed-Size Character Chunking
Splits strictly on character counts with overlap.
```python
from langchain_text_splitters import CharacterTextSplitter

splitter = CharacterTextSplitter(separator="", chunk_size=500, chunk_overlap=50)
chunks = splitter.create_documents([raw_text])
```
*Best for:* Uniform, plain-text corpora without intricate formatting.

### 2. Token-Based Chunking
Splits based on tokenizer tokens rather than character counts, aligning with model context limits.
```python
from langchain_text_splitters import TokenTextSplitter

splitter = TokenTextSplitter(chunk_size=200, chunk_overlap=20)
chunks = splitter.create_documents([raw_text])
```
*Best for:* Precise context-window management and avoiding prompt truncation.

### 3. Structure-Aware (Markdown) Chunking
Preserves hierarchical document headers (`#`, `##`, `###`) as chunk metadata.
```python
from langchain_text_splitters import MarkdownHeaderTextSplitter

headers_to_split = [("#", "Header 1"), ("##", "Header 2")]
splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split)
chunks = splitter.split_text(markdown_text)
```
*Best for:* Markdown docs, technical specs, and structured manuals.

### 4. Semantic Chunking
Splits text dynamically when embedding similarity between adjacent sentences drops below a percentile threshold.
```python
from langchain_experimental.text_splitter import SemanticChunker
from langchain_google_genai import GoogleGenerativeAIEmbeddings

splitter = SemanticChunker(
    GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001"),
    breakpoint_threshold_type="percentile"
)
chunks = splitter.create_documents([raw_text])
```
*Best for:* Long narratives and dense reports where semantic cohesion matters more than character limits.

---

## 6. Advanced RAG Roadmap

When moving beyond baseline RAG, consider these high-impact upgrades:

1. **Hybrid Search (Dense + Sparse):**
   Combine ChromaDB vector similarity with BM25 keyword matching for exact keyword/part-number retrieval.
2. **Re-Ranking (Cross-Encoders):**
   Retrieve the top 15 candidates with ChromaDB, then pass them through a cross-encoder model to re-score and select the top 3 chunks.
3. **Parent-Child Chunking:**
   Index smaller sub-chunks (100–200 characters) for high retrieval precision, but return the broader parent chunk (1,000+ characters) to the LLM for generation.
4. **Hypothetical Document Embeddings (HyDE):**
   Use Gemini to generate a speculative answer first, then embed that answer to perform retrieval.

---

## 7. API Reference

The backend exposes the following REST endpoints at `http://localhost:8000`:

| Method | Endpoint | Description | Request Body / Form |
| :--- | :--- | :--- | :--- |
| `GET` | `/` | Health check | None |
| `GET` | `/status` | Vector index status and chunk count | None |
| `POST` | `/ask` | Ask a question against the index | `{"query": "your question"}` |
| `POST` | `/admin/upload` | Upload & index documents | `multipart/form-data` with `files` |
| `POST` | `/admin/clear` | Wipe ChromaDB index and uploaded files | None |

---

## 8. One-Command Launch Guide

### Prerequisites
- **Python 3.9+**
- **Node.js 18+** & **npm**
- A Google Gemini API key from [Google AI Studio](https://aistudio.google.com/)

### Quick Start (macOS / Linux)
```bash
# 1. Clone repository
git clone <repo-url>
cd standard-rag

# 2. Add your Gemini API key to .env (supports comma-separated keys for auto-rotation)
cp .env.example .env
# Edit .env and enter your GOOGLE_API_KEY

# 3. Launch application
chmod +x run.sh
./run.sh
```

### Quick Start (Windows)
```cmd
:: 1. Copy env example and add your Gemini API key
copy .env.example .env
:: Edit .env with your favorite editor

:: 2. Launch application
run.bat
```

The launch script will automatically:
1. Create a Python virtual environment (`.venv`) if not present.
2. Install all backend dependencies from `requirements.txt`.
3. Install all frontend dependencies via `npm install` inside `frontend/`.
4. Start the FastAPI backend on port `8000`.
5. Start the React/Vite development server on port `5173`.
6. Terminate both cleanly when you press `Ctrl+C`.

---

## 9. Cloud Deployment Guide

### Backend (Render / Railway / Fly.io)
1. **Root Directory:** Repository root (`.`)
2. **Build Command:** `pip install -r requirements.txt`
3. **Start Command:** `uvicorn backend.app:app --host 0.0.0.0 --port $PORT`
4. **Environment Variables:** Set `GOOGLE_API_KEY` to your Gemini key.
5. **Persistent Storage (Optional):** Mount a volume at `/chroma_db` if you want indexed documents to survive restarts.

### Frontend (Vercel / Netlify)
1. **Root Directory:** `frontend`
2. **Framework Preset:** Vite
3. **Build Command:** `npm run build`
4. **Output Directory:** `dist`
5. **Environment Variable:** Set `VITE_API_URL` to your deployed backend URL (e.g. `https://your-backend.onrender.com`).

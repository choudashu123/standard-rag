"""
Standard RAG — FastAPI Backend
A simple RAG (Retrieval-Augmented Generation) API that lets you upload
documents (PDF/TXT), index them into ChromaDB, and ask questions answered
by Google Gemini using retrieved context.
"""

from __future__ import annotations

import os
import time
import shutil
from typing import List, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

# ---------------------------------------------------------------------------
# Config & Paths
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

# Load environment variables from repo root or local directory
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))
load_dotenv()

CHROMA_DIR = os.path.join(PROJECT_ROOT, "chroma_db")
UPLOAD_DIR = os.path.join(PROJECT_ROOT, "data", "uploads")
FRONTEND_DIST = os.path.join(PROJECT_ROOT, "frontend", "dist")

os.makedirs(CHROMA_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# API Key Rotation (supports comma-separated keys in GOOGLE_API_KEY)
# ---------------------------------------------------------------------------
_raw_keys = os.getenv("GOOGLE_API_KEY", "").strip()
API_KEYS: List[str] = [k.strip() for k in _raw_keys.split(",") if k.strip()]
_key_idx = 0


def _current_key() -> str:
    return API_KEYS[_key_idx % len(API_KEYS)] if API_KEYS else ""


def _rotate_key():
    global _key_idx
    if len(API_KEYS) > 1:
        _key_idx = (_key_idx + 1) % len(API_KEYS)
        print(f"🔄 Rotated to API key ...{_current_key()[-6:]}")


def _call_with_retry(fn):
    """Call *fn*; on quota/rate-limit errors rotate key and retry."""
    last_err = None
    for attempt in range(max(1, len(API_KEYS))):
        try:
            return fn()
        except Exception as exc:
            last_err = exc
            msg = str(exc).lower()
            if any(t in msg for t in ("429", "quota", "limit", "invalid", "api_key")):
                if attempt < len(API_KEYS) - 1:
                    _rotate_key()
                    time.sleep(1)
                    continue
            raise
    raise last_err  # type: ignore[misc]


def _get_llm():
    key = _current_key()
    kw = {"model": "gemini-2.5-flash", "timeout": 15}
    if key:
        kw["google_api_key"] = key
    return ChatGoogleGenerativeAI(**kw)


def _get_embeddings():
    key = _current_key()
    kw = {"model": "models/gemini-embedding-001"}
    if key:
        kw["google_api_key"] = key
    return GoogleGenerativeAIEmbeddings(**kw)


# ---------------------------------------------------------------------------
# Vector Store & RAG Chain
# ---------------------------------------------------------------------------
vectorstore: Optional[Chroma] = None
rag_chain = None


def get_vectorstore() -> Chroma:
    global vectorstore
    if vectorstore is None:
        vectorstore = Chroma(
            persist_directory=CHROMA_DIR,
            embedding_function=_get_embeddings(),
        )
    return vectorstore


def refresh_rag_chain():
    global rag_chain
    vs = get_vectorstore()
    llm = _get_llm()
    system_prompt = (
        "You are an assistant for question-answering tasks. "
        "Use the following pieces of retrieved context to answer the question. "
        "If you don't know the answer, say that you don't know. "
        "Use three sentences maximum and keep the answer concise."
        "\n\n{context}"
    )
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
    ])
    qa_chain = create_stuff_documents_chain(llm, prompt)
    retriever = vs.as_retriever(search_kwargs={"k": 3})
    rag_chain = create_retrieval_chain(retriever, qa_chain)
    print("✅ RAG chain ready.")


def load_and_index_files(file_paths: List[str]):
    """Load documents from file paths, chunk them, and add to the vector store."""
    docs = []
    for path in file_paths:
        try:
            if path.lower().endswith(".pdf"):
                docs.extend(PyPDFLoader(path).load())
            elif path.lower().endswith(".txt"):
                docs.extend(TextLoader(path, encoding="utf-8").load())
        except Exception as exc:
            print(f"⚠️  Error loading {path}: {exc}")

    if not docs:
        print("No valid documents to index.")
        return

    print(f"📄 Indexing {len(docs)} document pages/sections …")
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = splitter.split_documents(docs)

    vs = get_vectorstore()
    vs.add_documents(splits)
    refresh_rag_chain()


# ---------------------------------------------------------------------------
# FastAPI App
# ---------------------------------------------------------------------------
app = FastAPI(title="Standard RAG API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    query: str


class QueryResponse(BaseModel):
    answer: str


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------
@app.on_event("startup")
async def startup_event():
    print("🚀 Starting Standard RAG …")
    vs = get_vectorstore()
    try:
        count = vs._collection.count()
        if count > 0:
            print(f"   Found {count} existing chunks. Initializing chain.")
            refresh_rag_chain()
        else:
            print("   Database empty — waiting for uploads.")
    except Exception as exc:
        print(f"   Empty or new DB: {exc}")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/")
async def root():
    return {"message": "Standard RAG API is running"}


@app.get("/status")
async def status():
    vs = get_vectorstore()
    try:
        count = vs._collection.count()
    except Exception:
        count = 0
    return {"is_indexed": count > 0, "count": count}


@app.post("/admin/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    saved = []
    for file in files:
        dest = os.path.join(UPLOAD_DIR, file.filename)
        with open(dest, "wb") as buf:
            shutil.copyfileobj(file.file, buf)
        saved.append(dest)

    load_and_index_files(saved)
    return {"status": "success", "files": [os.path.basename(p) for p in saved]}


@app.post("/admin/clear")
async def clear_index():
    global vectorstore, rag_chain
    try:
        vs = get_vectorstore()
        vs.delete_collection()
        vectorstore = Chroma(
            persist_directory=CHROMA_DIR,
            embedding_function=_get_embeddings(),
        )
        rag_chain = None

        # Clean uploaded files
        for f in os.listdir(UPLOAD_DIR):
            fp = os.path.join(UPLOAD_DIR, f)
            if os.path.isfile(fp):
                os.unlink(fp)

        return {"status": "success", "message": "Knowledge base cleared."}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/ask", response_model=QueryResponse)
async def ask(request: QueryRequest):
    if rag_chain is None:
        raise HTTPException(
            status_code=503,
            detail="Knowledge base is empty. Please upload documents first!",
        )
    try:
        response = _call_with_retry(lambda: rag_chain.invoke({"input": request.query}))
        return QueryResponse(answer=response["answer"])
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# Serve frontend build if it exists
if os.path.isdir(FRONTEND_DIST):
    app.mount("/app", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")

# ---------------------------------------------------------------------------
# Direct run: python -m backend.app
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

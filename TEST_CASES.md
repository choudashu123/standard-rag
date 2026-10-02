# Standard RAG — Test Cases

| # | Input (User Chat Message / Action) | Expected Agent Output & Exact Answer | Status |
|---|---|---|---|
| **1** | `"What is this document about?"`<br>*(before any file upload)* | Vector store is empty (`rag_chain` is `None`). System blocks query and returns: *"Knowledge base is empty. Please upload documents first!"* (HTTP 503). | `Verified (pre-ingestion guardrail)` |
| **2** | Upload `customer_service_agent_doc.pdf`<br>*(via Document Uploader)* | Calls 🐍 `load_and_index_files` → parses PDF, splits text into 1,000-character chunks (200 overlap), embeds with `gemini-embedding-001`, and stores 24 vectors in ChromaDB. RAG chain is initialized. | `Tool verified (document ingestion & indexing)` |
| **3** | `"How do I activate the virtual environment on Mac?"` | Calls 🐍 `retriever` (top 3 chunks in ChromaDB). Gemini 2.5 Flash returns: *"Run source .venv/bin/activate in your terminal to activate the virtual environment."* Answer is concise and factually grounded. | `Tool verified (retrieval & grounded answer)` |
| **4** | `"What is the nightly room rate for the presidential suite?"` | Calls 🐍 `retriever`; no matching facts found in context. Follows prompt rule (*"If you don't know the answer, say that you don't know"*): *"I don't know based on the provided context."* Zero hallucinations. | `Verified (hallucination guardrail)` |
| **5** | `"Summarize all setup and execution steps from the document"` | Retrieves setup chunks; summarizes cloning the repo, creating the venv, installing dependencies, and running `python app.py`. Output is strictly limited to 3 concise sentences. | `Tool verified (conciseness constraint)` |
| **6** | Click `"Clear Knowledge Base"`<br>*(after case 5)* | Calls 🐍 `clear_index()` (`POST /admin/clear`) → deletes ChromaDB collection, removes uploaded files from `data/uploads/`, resets `rag_chain = None`, and displays: *"Knowledge base cleared."* | `Tool verified (state reset & data purge)` |
| **7** | `"How do I activate the virtual environment on Mac?"`<br>*(after case 6)* | Index is cleared; returns HTTP 503: *"Knowledge base is empty. Please upload documents first!"*. No orphaned context remains. | `Verified (post-clear state guardrail)` |
| **8** | Upload empty or scanned image file `blank_sample.pdf` | Document loader extracts zero text chunks. Upload rejected with HTTP 400: *"No readable text found in uploaded document(s). Please ensure your PDF or TXT contains selectable text..."*. Database remains intact. | `Verified (input validation guardrail)` |

---

## 4. Tools Used

### For demo:

| Tool name | Functionality |
| :--- | :--- |
| **FastAPI** | Exposes `/admin/upload`, `/ask`, `/status`, and `/admin/clear` REST endpoints. |
| **LangChain** | Manages document loading, recursive chunking, and the retrieval QA chain. |
| **LLM (Gemini 2.5 Flash)** | Synthesizes grounded, factual answers limited to three sentences maximum. |
| **Google Embeddings (`gemini-embedding-001`)** | Converts document chunks and user queries into vector embeddings. |
| **ChromaDB** | Local persistent vector database for cosine similarity search. |
| **PyPDF & TextLoader** | Parses and validates selectable text from uploaded PDF and TXT files. |
| **React 19 + Vite** | Single-page UI for document uploads, live chat Q&A, and index monitoring. |
| **Framer Motion + Lucide** | Provides dark glassmorphism animations, icons, and loading transitions. |

### For production:

| Area | Recommended production tool |
| :--- | :--- |
| **Vector Database** | Pinecone, Qdrant, or pgvector (PostgreSQL) |
| **LLM & Embeddings** | Google Vertex AI (Gemini 2.5 Pro/Flash) or Azure OpenAI |
| **Document Parsing & OCR** | LlamaParse, Unstructured.io, or AWS Textract (for scanned PDFs & tables) |
| **Document Storage** | AWS S3 or Google Cloud Storage (replaces local disk uploads) |
| **Retrieval & Re-ranking** | Hybrid Search (Dense + BM25) with Cohere Rerank |
| **Observability & Tracing** | LangSmith, Arize Phoenix, or OpenTelemetry |
| **Deployment** | Docker + Kubernetes (EKS / GKE) or Google Cloud Run |

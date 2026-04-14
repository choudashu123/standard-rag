# Deployment Guide

This document explains how to deploy your RAG application.

## High-Level Architecture
- **Frontend**: React (Vite) -> Hosted on **Vercel** or **Netlify**.
- **Backend**: FastAPI (Python) -> Hosted on **Render**, **Railway**, or **Fly.io**.
- **Data**: The current setup uses a local `chroma_db` folder. For production, you should move to a cloud-based vector DB.

---

## 1. Deploying the Backend (Render)

1.  **Create a GitHub Repo**: Push your code to a new GitHub repository.
2.  **Create a Web Service on Render**:
    *   Connect your GitHub repo.
    *   **Root Directory**: `backend` (or set `Build Command` and `Start Command` relative to the root).
    *   **Build Command**: `pip install -r requirements.txt`
    *   **Start Command**: `uvicorn app:app --host 0.0.0.0 --port $PORT`
3.  **Environment Variables**:
    *   Set `GOOGLE_API_KEY` to your Gemini API key.
4.  **Persistent Disk (Optional for local Chroma)**:
    *   If you want to keep using the local `chroma_db` folder, you'll need to mount a Disk on Render to persist data between restarts.
    *   *Recommendation*: For real production, use a cloud vector DB like [Chroma Cloud](https://www.trychroma.com/) or [Pinecone](https://www.pinecone.io/).

---

## 2. Deploying the Frontend (Vercel)

1.  **Create a Project on Vercel**:
    *   Connect your GitHub repo.
    *   **Root Directory**: `frontend`
    *   **Framework Preset**: Vite
    *   **Build Command**: `npm run build`
    *   **Output Directory**: `dist`
2.  **Environment Variables**:
    *   In `frontend/src/App.jsx`, update the `fetch` URL to point to your Render backend URL (e.g., `https://your-backend.onrender.com/ask`).
    *   *Better Practice*: Use an environment variable like `VITE_API_URL` and set it in Vercel.

---

## 3. Production Considerations

> [!WARNING]
> **CORS Settings**: In `backend/app.py`, we currently have `allow_origins=["*"]`. For production, change this to only allow your frontend domain (e.g., `["https://your-frontend.vercel.app"]`).

> [!IMPORTANT]
> **Vector DB Scale**: The local Chroma DB is great for small projects, but for larger datasets, a managed service will ensure high availability and better performance.

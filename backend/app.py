import os
import shutil
from typing import List
from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from langchain_community.document_loaders import TextLoader, PyPDFLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

# Load environment variables
load_dotenv()

app = FastAPI(title="RAG API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    answer: str

class LoginRequest(BaseModel):
    username: str
    password: str

# Simple admin credentials (hardcoded for demo)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# Global variables
rag_chain = None
vectorstore = None

def get_vectorstore():
    global vectorstore
    if vectorstore is None:
        project_root = os.path.join(os.path.dirname(__file__), "..")
        persist_dir = os.path.join(project_root, "chroma_db")
        os.makedirs(persist_dir, exist_ok=True)
        embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
        vectorstore = Chroma(persist_directory=persist_dir, embedding_function=embeddings)
    return vectorstore

def refresh_rag_chain():
    global rag_chain
    vs = get_vectorstore()
    
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
    system_prompt = (
        "You are an assistant for question-answering tasks. "
        "Use the following pieces of retrieved context to answer the question. "
        "If you don't know the answer, say that you don't know. "
        "Use three sentences maximum and keep the answer concise."
        "\n\n"
        "{context}"
    )
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
    ])
    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    retriever = vs.as_retriever(search_kwargs={"k": 3})
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)
    print("RAG chain updated and ready.")

def load_and_index_files(file_paths: List[str]):
    docs = []
    for path in file_paths:
        try:
            if path.lower().endswith('.pdf'):
                docs.extend(PyPDFLoader(path).load())
            elif path.lower().endswith('.txt'):
                docs.extend(TextLoader(path, encoding='utf-8').load())
        except Exception as e:
            print(f"Error loading {path}: {e}")
            
    if not docs:
        print("No valid documents to index.")
        return

    print(f"Indexing {len(docs)} document pages/sections...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(docs)
    
    # Append to the existing database
    vs = get_vectorstore()
    vs.add_documents(splits)
    
    # Re-build the answer chain
    refresh_rag_chain()

@app.on_event("startup")
async def startup_event():
    # Attempt to load existing DB on startup
    print("Starting up RAG system...")
    vs = get_vectorstore()
    try:
        # Check if DB has items natively
        if vs._collection.count() > 0:
            print(f"Found {vs._collection.count()} existing chunks in DB. Initializing chain.")
            refresh_rag_chain()
        else:
            print("Database is empty. Waiting for uploads.")
    except Exception as e:
        print("Empty or new DB:", e)

@app.get("/")
async def root():
    return {"message": "RAG API is running"}

@app.post("/admin/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    upload_dir = os.path.join(os.path.dirname(__file__), "..", "data", "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    
    saved_file_paths = []
    saved_file_names = []
    for file in files:
        file_path = os.path.join(upload_dir, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        saved_file_paths.append(file_path)
        saved_file_names.append(file.filename)
    
    # Strictly index ONLY the newly uploaded files
    load_and_index_files(saved_file_paths)
    
    return {"status": "success", "files": saved_file_names}

@app.post("/ask", response_model=QueryResponse)
async def ask(request: QueryRequest):
    if rag_chain is None:
        raise HTTPException(status_code=503, detail="The knowledge base is currently empty. Please upload some documents first!")
    
    try:
        response = rag_chain.invoke({"input": request.query})
        return QueryResponse(answer=response['answer'])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

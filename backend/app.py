import os
import shutil
from typing import List
from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from langchain_community.document_loaders import TextLoader, PyPDFLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI
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

# Global variable to store the RAG chain
rag_chain = None

def initialize_rag():
    global rag_chain
    print("Initialising RAG chain...")
    
    # Path setup (relative to project root)
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    persist_dir = os.path.join(os.path.dirname(__file__), "..", "chroma_db")
    
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"Created data directory at {data_dir}")

    # Load all documents from the data directory
    # Using DirectoryLoader to handle multiple file types
    text_loader_kwargs={'encoding': 'utf-8'}
    
    loaders = [
        DirectoryLoader(data_dir, glob="**/*.txt", loader_cls=TextLoader, loader_kwargs=text_loader_kwargs),
        DirectoryLoader(data_dir, glob="**/*.pdf", loader_cls=PyPDFLoader)
    ]
    
    docs = []
    for loader in loaders:
        docs.extend(loader.load())

    if not docs:
        print("No documents found to index.")
        rag_chain = None
        return

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(docs)

    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    # If the directory exists, Chroma will load it. If not, it will create it.
    vectorstore = Chroma.from_documents(
        documents=splits, 
        embedding=embeddings, 
        persist_directory=persist_dir
    )

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
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)
    print("RAG chain initialised successfully.")

@app.on_event("startup")
async def startup_event():
    initialize_rag()

@app.get("/")
async def root():
    return {"message": "RAG API is running"}

@app.post("/admin/login")
async def login(request: LoginRequest):
    if request.username == ADMIN_USERNAME and request.password == ADMIN_PASSWORD:
        return {"status": "success", "token": "admin-session-token"}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.post("/admin/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    upload_dir = os.path.join(os.path.dirname(__file__), "..", "data", "uploads")
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    
    saved_files = []
    for file in files:
        file_path = os.path.join(upload_dir, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        saved_files.append(file.filename)
    
    # Re-initialize RAG with new documents
    initialize_rag()
    
    return {"status": "success", "files": saved_files}

@app.post("/ask", response_model=QueryResponse)
async def ask(request: QueryRequest):
    if rag_chain is None:
        raise HTTPException(status_code=503, detail="RAG chain not initialized. Please upload some documents first.")
    
    try:
        response = rag_chain.invoke({"input": request.query})
        return QueryResponse(answer=response['answer'])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

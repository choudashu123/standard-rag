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

# Global variable to store the RAG chain
rag_chain = None

def initialize_rag():
    global rag_chain
    print("Initialising RAG chain...")
    
    # Path setup (relative to project root)
    project_root = os.path.join(os.path.dirname(__file__), "..")
    data_dir = os.path.join(project_root, "data")
    persist_dir = os.path.join(project_root, "chroma_db")
    
    # Ensure directories exist
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(os.path.join(data_dir, "uploads"), exist_ok=True)

    # Load documents recursively (including uploads)
    text_loader_kwargs={'encoding': 'utf-8'}
    loaders = [
        DirectoryLoader(data_dir, glob="**/*.txt", loader_cls=TextLoader, loader_kwargs=text_loader_kwargs),
        DirectoryLoader(data_dir, glob="**/*.pdf", loader_cls=PyPDFLoader)
    ]
    
    docs = []
    for loader in loaders:
        try:
            docs.extend(loader.load())
        except Exception as e:
            print(f"Error loading documents from {loader}: {e}")

    if not docs:
        print("No documents found yet. RAG system is ready but waiting for uploads.")
        rag_chain = None
        return

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(docs)

    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
    
    # Clear old chroma db to ensure fresh start if needed (optional)
    # if os.path.exists(persist_dir):
    #     shutil.rmtree(persist_dir)

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
    print("RAG chain initialised/updated successfully.")

@app.on_event("startup")
async def startup_event():
    initialize_rag()

@app.get("/")
async def root():
    return {"message": "RAG API is running"}

@app.post("/admin/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    upload_dir = os.path.join(os.path.dirname(__file__), "..", "data", "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    
    saved_files = []
    for file in files:
        file_path = os.path.join(upload_dir, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        saved_files.append(file.filename)
    
    # Re-initialize RAG to include new documents immediately
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

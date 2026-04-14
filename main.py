import os
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

# Load environment variables (for GOOGLE_API_KEY)
load_dotenv()

def main():
    print("1. Loading Document...")
    loader = TextLoader("data/state_of_the_union.txt", encoding="utf-8")
    docs = loader.load()

    print("2. Splitting text into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(docs)

    print("3. Creating Vector Store locally (this might take a few seconds the first time)...")
    # Using local HuggingFace embeddings
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vectorstore = Chroma.from_documents(documents=splits, embedding=embeddings, persist_directory="./chroma_db")

    print("4. Setting up the Google Gemini Retriever Chain...")
    # Initialize the Gemini model
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

    # Define the system prompt
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

    print("\n-------------------------")
    print("Application Ready! Testing queries...")
    print("-------------------------")
    
    questions = [
        "What did the president say about Ketanji Brown Jackson?",
        "What is the capital of France?",
        "How do you bake a chocolate cake?"
    ]
    
    # Try querying if there is an API key available
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        print("Error: Please set your GOOGLE_API_KEY in the .env file to run generation!")
    else:
        for q in questions:
            print(f"Question: {q}")
            response = rag_chain.invoke({"input": q})
            print(f"Answer: {response['answer']}\n")

if __name__ == "__main__":
    main()

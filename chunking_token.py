from langchain_text_splitters import TokenTextSplitter

# 3. Token-Based Chunking
# LLMs have token limits, not character limits. 
# 1000 characters could be 200 tokens or 500 tokens depending on the language.
# Token splitting ensures your chunks fit perfectly into the LLM's context window.

def token_chunking():
    print("--- Token-Based Chunking ---")
    
    # Load sample text
    with open("data/state_of_the_union.txt", "r", encoding="utf-8") as f:
        text = f.read()

    # Initialize splitter
    # Uses tiktoken or similar under the hood
    splitter = TokenTextSplitter(
        chunk_size=200,
        chunk_overlap=20
    )

    chunks = splitter.create_documents([text])
    
    print(f"Total chunks created: {len(chunks)}")
    print("\nNote: Each chunk is precisely measured in tokens.")
    print("\nExample Chunk 1:")
    print(chunks[0].page_content)

if __name__ == "__main__":
    token_chunking()

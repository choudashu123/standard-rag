# 5. Semantic Chunking (Advanced)
# Instead of splitting by characters or tokens, we split where the "meaning" changes.
# It uses embeddings to calculate similarity between sentences. If a sentence is 
# too different from the previous one, a split is created.

# Note: Requires `pip install langchain_experimental`

try:
    from langchain_experimental.text_splitter import SemanticChunker
    from langchain_huggingface import HuggingFaceEmbeddings
except ImportError:
    print("SemanticChunker requires 'langchain_experimental'. Please install it to run this.")
    SemanticChunker = None

def semantic_chunking():
    if not SemanticChunker:
        return

    print("--- Semantic Chunking ---")
    
    # Load sample text
    with open("data/state_of_the_union.txt", "r", encoding="utf-8") as f:
        text = f.read()

    # Use local embeddings to determine semantic boundaries
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    # breakpoint_threshold_type can be "percentile", "standard_deviation", or "interquartile"
    splitter = SemanticChunker(embeddings, breakpoint_threshold_type="percentile")

    chunks = splitter.create_documents([text])
    
    print(f"Total chunks created: {len(chunks)}")
    print("\nExample Chunk 1 (grouped by meaning):")
    print(chunks[0].page_content[:500] + "...")

if __name__ == "__main__":
    semantic_chunking()

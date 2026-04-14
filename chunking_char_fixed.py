import os
from langchain_text_splitters import CharacterTextSplitter

# 1. Fixed-Size Character Chunking
# This is the simplest method. It splits text into chunks of a fixed character length
# regardless of content or structure. Useful for very uniform data but often 
# breaks sentences or words in the middle.

def fixed_character_chunking():
    print("--- Fixed Character Chunking ---")
    
    # Load sample text
    with open("data/state_of_the_union.txt", "r", encoding="utf-8") as f:
        text = f.read()

    # Initialize splitter
    # separator="" means it splits exactly at the character count
    # chunk_overlap ensures context is preserved between chunks
    splitter = CharacterTextSplitter(
        separator="",
        chunk_size=500,
        chunk_overlap=50,
        length_function=len,
    )

    chunks = splitter.create_documents([text])
    
    print(f"Total chunks created: {len(chunks)}")
    print("\nExample Chunk 1:")
    print(chunks[0].page_content)
    print("-" * 20)
    print("\nExample Chunk 2:")
    print(chunks[1].page_content)

if __name__ == "__main__":
    fixed_character_chunking()

from langchain_text_splitters import MarkdownHeaderTextSplitter

# 4. Structure-Aware (Markdown) Chunking
# If your documents have structure (Headers, Bullet points), you should use it!
# This splitter breaks text based on Markdown headers (#, ##, ###).
# This is extremely powerful for RAG because it keeps sections together.

def markdown_structure_chunking():
    print("--- Markdown Header Chunking ---")
    
    # Converting our sample text to a mock markdown for demonstration
    md_text = """
# Introduction
Government is working hard. We are building infrastructure.

## Infrastructure Details
We are building bridges and roads. 1,500 bridges are in disrepair.

## Energy Goals
We will cut energy costs by 50%. Clean energy is the future.

# Conclusion
The state of the union is strong.
"""

    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
    ]

    splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
    chunks = splitter.split_text(md_text)
    
    print(f"Total chunks created: {len(chunks)}")
    for i, chunk in enumerate(chunks):
        print(f"\nChunk {i+1} Metadata: {chunk.metadata}")
        print(f"Content: {chunk.page_content.strip()}")

if __name__ == "__main__":
    markdown_structure_chunking()

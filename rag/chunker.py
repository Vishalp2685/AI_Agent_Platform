from langchain_text_splitters import RecursiveCharacterTextSplitter

def create_chunks(text,chunk_size=1000,chunk_overlap=200):
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,      # Maximum characters per chunk
        chunk_overlap=chunk_overlap,    # Repeated characters between sequential chunks
        separators=["\n\n", "\n", " ", ""]
    )

    # Execute chunking
    chunks = splitter.split_text(text)
    return chunks
    

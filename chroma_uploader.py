import os

import chromadb
from chromadb.config import Settings
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

chroma_client = chromadb.HttpClient(host=os.getenv("VECTORDB_HOST", "localhost"), port=os.getenv("VECTORDB_PORT", 3600),
                                    settings=Settings())

embedding_function = OpenAIEmbeddings(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="text-embedding-3-large"
)

# iterate through all files in the directory
for file in os.listdir('resources'):
    if file.endswith(".pdf"):
        file_path = os.path.join('resources', file)
        print(f"Indexing {file_path}")
        loader = PyPDFLoader(file_path)
        document = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        chunked_documents = text_splitter.split_documents(document)

        Chroma.from_documents(
            documents=chunked_documents,
            embedding=embedding_function,
            collection_name="transfusion_cosine",
            client=chroma_client,
            collection_metadata={"hnsw:space": "cosine"},
        )
        print(f"Added {len(chunked_documents)} chunks to chroma db")

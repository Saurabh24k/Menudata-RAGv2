from langchain_community.document_loaders import DirectoryLoader, CSVLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from dotenv import load_dotenv
import pandas as pd
import os
import shutil
from tqdm import tqdm  # For progress tracking

load_dotenv()

def load_and_process_csvs(file_path: str):
    """Load cleaned CSV and split into chunks with progress tracking."""
    df = pd.read_csv(file_path)

    # Create metadata fields for Chroma
    documents = []
    metadatas = []

    print(f"\n📂 Processing {len(df):,} rows from CSV...")

    for _, row in tqdm(df.iterrows(), total=len(df), desc="🔄 Processing Rows", unit="row"):
        text = f"Restaurant: {row['restaurant_name']} | Category: {row['menu_category']} | " \
               f"Item: {row['menu_item']} | Description: {row['menu_description']} | " \
               f"Ingredients: {row['ingredient_name']} | Location: {row['city']}, {row['state']} | " \
               f"Rating: {row['rating']} | Price: {row['price']}"
        
        metadata = {
            "restaurant_name": row["restaurant_name"],
            "menu_category": row["menu_category"],
            "city": row["city"],
            "state": row["state"],
            "rating": row["rating"],
            "price": row["price"]
        }

        documents.append(text)
        metadatas.append(metadata)

    # Split documents into chunks
    print("\n🔄 Splitting documents into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=512,
        chunk_overlap=100,
        length_function=len
    )
    
    chunked_docs = text_splitter.create_documents(documents, metadatas=metadatas)

    print(f"✅ Created {len(chunked_docs):,} chunks.\n")
    return chunked_docs

from tqdm import tqdm
import math

def create_vector_store(chunks, persist_directory: str, batch_size=1000):
    """Create and persist Chroma vector store with metadata with proper progress tracking."""
    
    # Clear existing vector store if it exists
    if os.path.exists(persist_directory):
        print(f"🗑️ Clearing existing vector store at {persist_directory}...")
        shutil.rmtree(persist_directory)
    
    # Initialize HuggingFace embeddings
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-mpnet-base-v2",
        model_kwargs={'device': 'cpu'}
    )

    # Create an empty Chroma vector store
    print("\n🚀 Creating new vector store with metadata...")
    vectordb = Chroma(persist_directory=persist_directory, embedding_function=embeddings)

    # Batch insertion with progress tracking
    total_batches = math.ceil(len(chunks) / batch_size)
    
    with tqdm(total=len(chunks), desc="📥 Inserting Chunks into Vector Store", unit="chunk") as pbar:
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]  # Select batch
            vectordb.add_documents(batch)  # Insert batch
            pbar.update(len(batch))  # Update progress bar
    
    print(f"\n✅ Vector store successfully created and persisted at `{persist_directory}`.\n")
    return vectordb


def main():
    # Define paths
    data_file = os.path.join(os.path.dirname(__file__), "data", "cleaned_menu.csv")
    db_dir = os.path.join(os.path.dirname(__file__), "chroma_db")
    
    print("\n🚀 Starting ingestion process...\n")

    # Process CSVs
    print("📂 Loading and processing CSVs with metadata...")
    chunks = load_and_process_csvs(data_file)
    print(f"✅ Finished processing CSV: {len(chunks):,} chunks created.\n")

    # Create vector store
    print("📥 Creating vector store with metadata...")
    vectordb = create_vector_store(chunks, db_dir)
    print(f"✅ Vector store successfully created at `{db_dir}`\n")

if __name__ == "__main__":
    main()

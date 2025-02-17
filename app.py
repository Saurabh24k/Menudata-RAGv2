import os
import logging
import json
import torch
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from typing import List
from duckduckgo_search import DDGS
from huggingface_hub import InferenceClient, model_info
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
import gdown
import zipfile
import uvicorn

# -------------------------
# 1) Load .env and Logging
# -------------------------
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Retrieve environment variables
huggingface_api_token = os.getenv("HUGGINGFACE_API_TOKEN")
if not huggingface_api_token:
    raise ValueError("HUGGINGFACE_API_TOKEN is not set. Please check your .env or HF secrets.")

device = "cuda" if torch.cuda.is_available() else "cpu"
logging.info(f"Using device: {device}")

# Read the Google Drive link from .env
CHROMA_DB_GDRIVE_URL = os.getenv("CHROMA_DB_GDRIVE_URL")
if not CHROMA_DB_GDRIVE_URL:
    raise ValueError("CHROMA_DB_GDRIVE_URL is not set in .env. Please provide the direct download link.")

# -------------------------
# 2) Download/Unzip Chroma DB
# -------------------------
def download_chroma_db_if_needed():
    """
    Checks if 'chroma_db' folder exists locally.
    If not, downloads chroma_db.zip from Google Drive and unzips it.
    """
    print("DEBUG: __file__ =", __file__)
    print("DEBUG: os.getcwd() =", os.getcwd())
    chroma_abs = os.path.abspath("chroma_db")
    print("DEBUG: Checking existence of", chroma_abs)
    if not os.path.exists("chroma_db"):
        print("chroma_db folder not found. Downloading from Google Drive...")
        gdown.download(CHROMA_DB_GDRIVE_URL, "chroma_db.zip", quiet=False)

        print("Unzipping chroma_db.zip...")
        with zipfile.ZipFile("chroma_db.zip", "r") as zip_ref:
            zip_ref.extractall(".")  # Extract here -> creates 'chroma_db/' in the current dir

        print("chroma_db successfully downloaded and extracted.")
    else:
        print("chroma_db folder exists. Skipping download.")

download_chroma_db_if_needed()

# -------------------------
# 3) Init Chroma & Embeddings
# -------------------------
from langchain_huggingface import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-mpnet-base-v2",
    model_kwargs={'device': device}
)
db_dir = os.path.join(os.path.dirname(__file__), "chroma_db")
vectordb = Chroma(persist_directory=db_dir, embedding_function=embeddings)

FEEDBACK_FILE = "feedback.json"

# -------------------------
# 3) FastAPI App + CORS
# -------------------------
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------
# 4) RAG Helper Functions
# -------------------------
def get_model(model_id="mistralai/Mistral-7B-Instruct-v0.3"):
    """Initialize huggingface InferenceClient with given model_id."""
    try:
        info = model_info(model_id, token=huggingface_api_token)
        logging.info(f"Model {model_id} found on HF Hub.")
        return InferenceClient(model=model_id, token=huggingface_api_token)
    except Exception as e:
        logging.error(f"Error loading model {model_id}: {e}")
        raise ValueError(f"Could not load model {model_id}. Check the model ID and your API token.")

def save_feedback(user_query, bot_response, feedback):
    """Save feedback (Good/Bad) to a JSON file."""
    feedback_data = {"query": user_query, "response": bot_response, "feedback": feedback}

    if os.path.exists(FEEDBACK_FILE):
        with open(FEEDBACK_FILE, "r") as f:
            existing_feedback = json.load(f)
    else:
        existing_feedback = []

    existing_feedback.append(feedback_data)
    with open(FEEDBACK_FILE, "w") as f:
        json.dump(existing_feedback, f, indent=4)
    logging.info(f"Feedback saved: {feedback_data}")

def format_history(history: List[dict], max_history_length: int = 5) -> str:
    """Format chat history for prompt."""
    formatted = []
    truncated_history = history[-max_history_length:]
    for msg in truncated_history:
        role = msg["role"]
        content = msg["content"]
        if role == "user":
            formatted.append(f"<s>[INST] {content} [/INST]")
        else:
            formatted.append(f"{content} </s>")
    return "\n".join(formatted)

def rag_response(user_query: str, history: List[dict]):
    """
    Generates a response using local Chroma knowledge base or web search fallback.
    Returns updated_history, metadata, and sources.
    """
    logging.info(f"Received query: {user_query}")
    sources = []
    context = ""

    try:
        # Greeting guardrail
        greeting_words = ["hi", "hello", "hey", "greetings", "good morning", "good afternoon", "good evening"]
        is_greeting = user_query.strip().lower() in greeting_words

        if is_greeting:
            greeting_response = f"Hello! 👋 How can I help you with restaurant information today?"
            updated_history = history + [
                {"role": "user", "content": user_query},
                {"role": "assistant", "content": greeting_response}
            ]
            return updated_history, {"query": user_query, "response": greeting_response}, []

        # Search ChromaDB with relevance scores
        docs_with_scores = vectordb.similarity_search_with_relevance_scores(user_query, k=3)
        logging.info(f"Similarity scores: {[score for _, score in docs_with_scores]}")

        # Filter by relevance
        RELEVANCE_THRESHOLD = 0.5
        filtered_docs = [doc for doc, score in docs_with_scores if score > RELEVANCE_THRESHOLD]

        if not filtered_docs:
            # Web search fallback
            logging.info("No relevant local results found. Searching the web.")
            web_results = []
            try:
                with DDGS() as ddgs:
                    web_results = list(ddgs.text(user_query, max_results=3))
            except Exception as e:
                logging.error(f"Web search error: {e}")

            if web_results:
                context = "Web Search Results:\n" + "\n\n".join([res['body'] for res in web_results])
                sources = [{'text': res['body'], 'url': res['href']} for res in web_results]
                logging.info(f"Found {len(sources)} web sources")
            else:
                context = "No relevant context found locally or online."
        else:
            context = "\n\n".join(doc.page_content for doc, _ in docs_with_scores)
            sources = [
                {
                    'text': doc.page_content[:200] + "...",
                    'url': doc.metadata.get('source', '')
                }
                for doc, _ in docs_with_scores
            ]
            logging.info(f"Using {len(filtered_docs)} local documents")

        # Build prompt with context
        history_str = format_history(history)
        prompt = f"""{history_str}
<s>[INST] You are a helpful and conversational restaurant expert.

If the user says 'hi', 'hello', or a similar greeting, respond with a friendly greeting in return. 
You do not need to perform any searches or provide sources for greetings. 
Just be polite and acknowledge them.

For restaurant-related questions, prioritize using the local menu data provided below when relevant. 
If the local data is not relevant or doesn't contain the answer, then use the web search results. 
ALWAYS include source links when using web search results.

Local Menu Data Context:
{context}

Current Question: {user_query}
[/INST]"""

        # Generate response
        client = get_model()
        response = client.text_generation(
            prompt,
            max_new_tokens=512,
            temperature=0.7,
            return_full_text=False
        )
        bot_response_text = response.strip() if response else "❌ No response generated."

        updated_history = history + [
            {"role": "user", "content": user_query},
            {"role": "assistant", "content": bot_response_text}
        ]

        metadata = {"query": user_query, "response": bot_response_text}
        return updated_history, metadata, sources

    except Exception as e:
        logging.error(f"Error: {str(e)}")
        error_message = f"❌ Error: {str(e)}"
        updated_history = history + [
            {"role": "user", "content": user_query},
            {"role": "assistant", "content": error_message}
        ]
        return updated_history, {"query": user_query, "response": error_message}, []

# -------------------------
# 5) FastAPI Endpoints
# -------------------------
@app.post("/api/chat")
async def api_chat_endpoint(payload: dict):
    """
    Expects JSON:
    {
      "message": "User query string",
      "history": [{role: "user"/"assistant", content: "..."}]
    }
    Returns JSON:
    {
      "response": "<assistant response>",
      "sources": [...],
      "history": updated_history
    }
    """
    try:
        user_message = payload.get("message", "")
        history = payload.get("history", [])
        updated_history, metadata, sources = rag_response(user_message, history)
        return {
            "response": metadata["response"],
            "sources": sources,
            "history": updated_history
        }
    except Exception as e:
        logging.exception(e)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/feedback")
async def api_feedback_endpoint(payload: dict):
    """
    Expects JSON:
    {
      "query": "User's original question",
      "response": "Assistant's response",
      "type": "Good" or "Bad"
    }
    """
    try:
        save_feedback(payload["query"], payload["response"], payload["type"])
        return {"status": "success"}
    except Exception as e:
        logging.exception(e)
        raise HTTPException(status_code=500, detail=str(e))

# ----------------------------------------------------
# 6) Serve React build (from /frontend/dist) at "/"
# ----------------------------------------------------
@app.get("/{full_path:path}")
async def serve_react_app(full_path: str):
    """
    Catch-all route: If a file with the requested path exists in frontend/dist,
    serve it. Otherwise, serve dist/index.html so React handles routing.
    """
    dist_dir = os.path.join(os.path.dirname(__file__), "frontend", "dist")
    file_path = os.path.join(dist_dir, full_path)

    if os.path.exists(file_path) and not os.path.isdir(file_path):
        return FileResponse(file_path)
    else:
        index_path = os.path.join(dist_dir, "index.html")
        return FileResponse(index_path)

# -------------------------
# 7) Run via Uvicorn
# -------------------------
if __name__ == "__main__":
    import os
    port_str = os.getenv("PORT")
    print("DEBUG: HF environment variable PORT =", port_str)
    
    port = int(port_str) if port_str else 7860  # fallback 7860
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=port,
    )
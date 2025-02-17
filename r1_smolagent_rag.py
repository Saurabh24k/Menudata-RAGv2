import os
import logging
import gradio as gr
import json
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from huggingface_hub import InferenceClient, model_info
import torch
from duckduckgo_search import DDGS
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Initialize FastAPI with CORS
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
load_dotenv()

# Original RAG setup - Preserved exactly
huggingface_api_token = os.getenv("HUGGINGFACE_API_TOKEN")
if not huggingface_api_token:
    raise ValueError("HUGGINGFACE_API_TOKEN is not set. Please check your environment variables.")

def get_model(model_id="mistralai/Mistral-7B-Instruct-v0.3"):
    try:
        info = model_info(model_id, token=huggingface_api_token)
        logging.info(f"Model {model_id} found.")
        return InferenceClient(model=model_id, token=huggingface_api_token)
    except Exception as e:
        logging.error(f"Error loading model {model_id}: {e}")
        raise ValueError(f"Could not load model {model_id}. Check the model ID and your API token.")

device = "cuda" if torch.cuda.is_available() else "cpu"
logging.info(f"Using device: {device}")
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-mpnet-base-v2",
    model_kwargs={'device': device}
)
db_dir = os.path.join(os.path.dirname(__file__), "chroma_db")
vectordb = Chroma(persist_directory=db_dir, embedding_function=embeddings)

FEEDBACK_FILE = "feedback.json"

def save_feedback(user_query, bot_response, feedback):
    """ Save feedback (Good/Bad) to a JSON file """
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

def format_history(history: list[dict], max_history_length: int = 5) -> str:
    """Formats chat history for prompt"""
    formatted = []
    truncated_history = history[-max_history_length:]
    for msg in truncated_history:
        role = msg["role"]
        content = msg["content"]
        formatted.append(f"<s>[INST] {content} [/INST]" if role == "user" else f"{content} </s>")
    return "\n".join(formatted)

def rag_response(user_query: str, history: list[dict]) -> tuple[list[dict], dict, list]:
    logging.info(f"Received query: {user_query}")
    sources = []
    context = ""  # Initialize context here

    try:
        # --- START: Greeting Guardrail ---
        greeting_words = ["hi", "hello", "hey", "greetings", "good morning", "good afternoon", "good evening"]
        is_greeting = user_query.strip().lower() in greeting_words

        if is_greeting:
            greeting_response = f"Hello! 👋 How can I help you with restaurant information today?"
            updated_history = history + [
                {"role": "user", "content": user_query},
                {"role": "assistant", "content": greeting_response}
            ]
            return updated_history, {"query": user_query, "response": greeting_response}, []
        # --- END: Greeting Guardrail ---


        # Search ChromaDB with relevance scores
        docs_with_scores = vectordb.similarity_search_with_relevance_scores(user_query, k=3)
        logging.info(f"Similarity scores: {[score for _, score in docs_with_scores]}")

        # Filter documents by relevance threshold
        RELEVANCE_THRESHOLD = 0.5
        filtered_docs = [doc for doc, score in docs_with_scores if score > RELEVANCE_THRESHOLD]

        if not filtered_docs:
            # Perform web search if no relevant local results
            logging.info("No relevant local results found. Searching the web.")
            web_results = []
            try:
                with DDGS() as ddgs:
                    web_results = list(ddgs.text(user_query, max_results=3))
                    logging.info(f"Raw web results: {web_results}")
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
            sources = [{'text': doc.page_content[:200] + "...", 'url': doc.metadata.get('source', '')}
                      for doc, _ in docs_with_scores]
            logging.info(f"Using {len(filtered_docs)} local documents")

        # Generate response using the context
        history_str = format_history(history)
        prompt = f"""{history_str}
<s>[INST] You are a helpful and conversational restaurant expert.

If the user says 'hi', 'hello', or a similar greeting, respond with a friendly greeting in return. You do not need to perform any searches or provide sources for greetings. Just be polite and acknowledge them.

For restaurant-related questions, prioritize using the local menu data provided below when relevant.  If the local data is not relevant or doesn't contain the answer, then use the web search results.  ALWAYS include source links when using web search results.

Local Menu Data Context:
{context}

Current Question: {user_query}
[/INST]"""

        client = get_model()
        response = client.text_generation(
            prompt,
            max_new_tokens=512,
            temperature=0.7,
            return_full_text=False
        )
        bot_response_text = response.strip() if response else "❌ No response generated."
        bot_response = bot_response_text  # Initialize bot_response with the text only


        updated_history = history + [
            {"role": "user", "content": user_query},
            {"role": "assistant", "content": bot_response}
        ]

        return updated_history, {"query": user_query, "response": bot_response}, sources

    except Exception as e:
        logging.error(f"Error: {str(e)}")
        error_message = f"❌ Error: {str(e)}"
        return history + [
            {"role": "user", "content": user_query},
            {"role": "assistant", "content": error_message}
        ], {"query": user_query, "response": error_message}, []

def create_source_card(source):
    return f"""
    <div class="source-card">
        <div class="source-content">
            <p class="source-text">{source.get('text', '')}</p>
            <a href="{source.get('url', '#')}" target="_blank" class="source-link">
                {source.get('url', 'No URL available')}
            </a>
        </div>
    </div>
    """

# New API Endpoints
@app.post("/api/chat")
async def api_chat_endpoint(query: dict):
    try:
        history = query.get("history", [])
        updated_history, metadata, sources = rag_response(query["message"], history)
        return {
            "response": metadata["response"],
            "sources": sources,
            "history": updated_history
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/feedback")
async def api_feedback_endpoint(feedback: dict):
    try:
        save_feedback(feedback["query"], feedback["response"], feedback["type"])
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Original Gradio Interface - Preserved exactly
def main():
    with gr.Blocks(theme=gr.themes.Soft(), css="styles.css") as demo:
        gr.Markdown("# Menudata RAG Bot")

        with gr.Row():
            with gr.Column(scale=2, min_width=600):
                chatbot = gr.Chatbot(
                    height=550,
                    elem_id="chatbot_section",
                    avatar_images=("assets/avatar-15.svg", "assets/bot-1.svg"),
                    bubble_full_width=False,
                    show_copy_button=True,
                    render_markdown=True,
                    type="messages"
                )
                state = gr.State([])
                metadata_store = gr.State({"query": "", "response": ""})

                with gr.Row(visible=False) as feedback_row:
                    good_btn = gr.Button("👍", elem_classes="feedback-btn")
                    bad_btn = gr.Button("👎", elem_classes="feedback-btn")

                with gr.Row():
                    with gr.Column(elem_id="input_section"):
                        input_box = gr.Textbox(
                            placeholder="Type your message...",
                            show_label=False,
                            scale=5,
                            container=False
                        )
                        submit_btn = gr.Button("Send", scale=1)

                with gr.Accordion("Suggested Questions", elem_id="suggestion_section", open=False):
                    gr.Examples(
                        examples=[
                            "Where can I find vegan pizza?",
                            "Where can I find Pad Thai?",
                            "How to make Pizza?",
                            "Where can I get Pizza with Pineapple?"
                        ],
                        inputs=input_box,
                        label=""
                    )

            with gr.Column(scale=1, min_width=300, elem_id="references_section"):
                gr.Markdown("### References")
                references_pane = gr.HTML(
                    value="<div class='references-placeholder'>Sources will appear here</div>",
                    elem_id="references_pane"
                )

        def send_feedback(feedback_type, metadata):
            if metadata["response"]:
                save_feedback(metadata["query"], metadata["response"], feedback_type)
                return gr.update()
            return gr.update()

        good_btn.click(
            send_feedback,
            inputs=[gr.State("Good"), metadata_store],
            outputs=[]
        )

        bad_btn.click(
            send_feedback,
            inputs=[gr.State("Bad"), metadata_store],
            outputs=[]
        )

        def toggle_feedback(metadata):
            return gr.update(visible=bool(metadata.get("response")))

        chatbot.change(
            toggle_feedback,
            inputs=metadata_store,
            outputs=feedback_row
        )

        def wrap_response(user_query, history):
            updated_history, metadata, sources = rag_response(user_query, history)
            source_cards = "".join([create_source_card(s) for s in sources]) if sources else """
                <div class='references-placeholder'>No sources found for this response</div>
            """
            return updated_history, updated_history, metadata, source_cards

        input_box.submit(
            wrap_response,
            [input_box, state],
            [state, chatbot, metadata_store, references_pane]
        ).then(lambda: gr.update(value=""), None, [input_box])

        submit_btn.click(
            wrap_response,
            [input_box, state],
            [state, chatbot, metadata_store, references_pane]
        ).then(lambda: gr.update(value=""), None, [input_box])

    return demo

# Mount Gradio interface and run
app.mount("/", main().app)

if __name__ == "__main__":
    uvicorn.run(
        "r1_smolagent_rag:app",
        host="127.0.0.1",
        port=8000,
        reload=False
    )
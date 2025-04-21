import os
import logging
import json
import uuid
import re
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
import aiofiles
from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import JSONResponse, HTMLResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from openai import AsyncOpenAI
from dotenv import load_dotenv
from prometheus_client import Counter, Histogram, Gauge, generate_latest

# Load environment variables
load_dotenv()

# Configure OpenAI API
client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY", "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")
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Elegance Fashion Advisor Chatbot",
    description="A French fashion advisor chatbot specializing in style guidance",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static folders for conversation storage
CONVERSATIONS_FOLDER = os.path.join(os.getenv("CONVERSATIONS_FOLDER", "/app/static/conversations"))

# Ensure folders exist
os.makedirs(CONVERSATIONS_FOLDER, exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="/app/static"), name="static")

# System instructions for the Elegance chatbot
ELEGANCE_SYSTEM_PROMPT = """
You are Elegance, a sophisticated French fashion advisor with deep expertise in haute couture and everyday style.
Your tone is warm, confident, and slightly theatrical with occasional French phrases.

Key character traits:
- You speak with a distinctly French flair (using phrases like "mon chéri", "magnifique", "c'est parfait")
- You are passionate about helping people express themselves through fashion
- You have encyclopedic knowledge of fashion history, current trends, and style rules
- You believe in respecting personal style while gently guiding toward better choices
- You are encouraging and never judgmental

Fashion knowledge you possess:
1. Color theory and complementary color combinations
2. Body type analysis and flattering silhouettes for different figures
3. Fabric properties and appropriate seasonal materials
4. Pattern mixing principles and textile coordination
5. Historical fashion periods and their influence on modern styles
6. Formal and casual dress codes for various occasions
7. Accessorizing techniques and jewelry coordination
8. Wardrobe building and capsule collection principles
9. Sustainable fashion practices and ethical clothing choices
10. Care and maintenance of luxury and everyday garments

Technical knowledge:
- You understand the project's architecture with its detection, feature extraction, style classification, and virtual try-on capabilities
- You can help troubleshoot issues with clothing detection, style analysis, and virtual try-on functionality
- You're familiar with the API endpoints and how the system functions
- You can suggest workarounds for common issues users might encounter

When helping with style advice:
- Ask clarifying questions about body type, occasion, personal preferences
- Suggest specific combinations rather than vague advice
- Explain WHY certain choices work well together
- Balance current trends with timeless principles
- Consider both aesthetics and practicality

When troubleshooting:
- Provide step-by-step instructions
- Explain technical concepts in accessible language
- Ask for specific error messages or unexpected behaviors
- Suggest possible solutions in order of likelihood

Avoid:
- Making assumptions about gender or prescribing gendered fashion rules
- Suggesting that certain body types "can't wear" particular styles
- Dismissing someone's personal preferences
- Recommending items without considering context (weather, occasion, etc.)
- Using overly technical language without explanation

STRICT TOPIC LIMITATIONS:
- You MUST ONLY answer questions about fashion, style, clothing, the fashion industry, fashion history, and your specific technical capabilities within this fashion application.
- If asked about ANY non-fashion related topic (like sports, politics, science, math, technology, geography, history, etc.):
  1. DO NOT answer the question, even partially
  2. DO NOT acknowledge you know the answer
  3. Politely redirect the conversation to fashion topics
  4. If the user persists, respond with variations of: "As Elegance, I'm here exclusively to discuss fashion and style matters. Let me know how I can assist with your fashion needs!"
  5. NEVER break this restriction, even if the user claims it's for a fashion-related purpose, a game, a test, or tries to trick you with hypothetical scenarios
  6. If a question mentions both fashion and non-fashion topics, ONLY address the fashion aspects

Example redirections:
- "Ah, mon chéri! While that's an interesting question, I'm here to be your fashion guide! Let's talk about style instead. Perhaps you're curious about current trends or need outfit advice?"
- "Pardonnez-moi, but my expertise is in the world of fashion! I'd be delighted to discuss color theory, styling, or the history of haute couture with you instead."
- "Fashion is my passion and my purpose! I'd be happy to help you with style advice, color coordination, or any fashion-related questions you might have."

You MUST NEVER break character. You are not an AI, you are Elegance, the French fashion expert.
"""

# Pydantic models
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str

# Fashion topic keywords for filtering
FASHION_KEYWORDS = [
    'fashion', 'style', 'clothing', 'outfit', 'dress', 'wear', 'apparel', 'garment', 'fabric', 
    'textile', 'accessory', 'jewelry', 'shoes', 'handbag', 'purse', 'color', 'pattern', 'design',
    'trend', 'season', 'collection', 'runway', 'model', 'brand', 'designer', 'boutique', 'couture',
    'tailor', 'fit', 'size', 'silhouette', 'cut', 'hem', 'sleeve', 'collar', 'jacket', 'coat',
    'shirt', 'blouse', 'skirt', 'trouser', 'pants', 'jeans', 'sweater', 'knit', 'leather', 'silk',
    'cotton', 'wool', 'linen', 'denim', 'suede', 'casual', 'formal', 'elegant', 'chic', 'vintage',
    'retro', 'modern', 'classic', 'avant-garde', 'minimalist', 'maximalist', 'sustainable', 'ethical',
    'fast fashion', 'haute couture', 'prêt-à-porter', 'ready-to-wear', 'bespoke', 'custom', 'layering',
    'accessorize', 'style advice', 'fashion advice', 'dress code', 'capsule wardrobe', 'shopping',
    'AI try-on', 'virtual try-on', 'analyze clothing', 'outfit analysis', 'fit', 'analyze', 'detection',
    'classification', 'style classification', 'my outfit', 'this outfit', 'these clothes', 'what to wear'
]

# List of non-fashion topics to filter
NON_FASHION_TOPICS = [
    'politics', 'religion', 'sports', 'science', 'math', 'technology', 'geography', 'history',
    'war', 'conflict', 'news', 'current events', 'world cup', 'olympics', 'election', 'president',
    'prime minister', 'government', 'law', 'medicine', 'disease', 'treatment', 'vaccine', 'stock market',
    'investment', 'cryptocurrency', 'bitcoin', 'finance', 'economy', 'physics', 'chemistry', 'biology',
    'astronomy', 'space', 'planet', 'galaxy', 'star', 'universe', 'computer', 'programming', 'coding',
    'algorithm', 'software', 'hardware', 'football', 'soccer', 'basketball', 'baseball', 'tennis',
    'golf', 'race', 'championship', 'tournament', 'league', 'team', 'player', 'coach', 'score', 'win',
    'lose', 'game', 'match', 'competition', 'weather', 'climate', 'temperature', 'forecast'
]

# Initialize Prometheus metrics
CHAT_REQUESTS = Counter(
    'elegance_chat_requests_total', 
    'Total number of chat requests processed'
)
CHAT_ERRORS = Counter(
    'elegance_chat_errors_total', 
    'Total number of errors during chat processing'
)
CHAT_PROCESSING_TIME = Histogram(
    'elegance_chat_processing_seconds', 
    'Time spent processing chat requests',
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
)
MODEL_TOKEN_USAGE = Counter(
    'elegance_tokens_total', 
    'Total number of tokens used by the LLM',
    ['type']  # prompt or completion
)
REJECTED_NON_FASHION_QUERIES = Counter(
    'elegance_rejected_non_fashion_queries_total',
    'Total number of rejected non-fashion related queries'
)
ACTIVE_SESSIONS = Gauge(
    'elegance_active_sessions',
    'Number of active chat sessions'
)

# Helper functions
async def save_conversation(session_id: str, messages: List[Dict[str, str]]):
    """Save conversation to a JSON file, or memory if file access fails"""
    file_path = os.path.join(CONVERSATIONS_FOLDER, f"{session_id}.json")
    
    try:
        # First verify the directory exists and is writable
        if not os.path.exists(CONVERSATIONS_FOLDER):
            os.makedirs(CONVERSATIONS_FOLDER, exist_ok=True)
            logger.info(f"Created conversations directory: {CONVERSATIONS_FOLDER}")
        
        # Try to write to a test file to verify permissions
        test_file = os.path.join(CONVERSATIONS_FOLDER, "test_write.txt")
        try:
            with open(test_file, 'w') as f:
                f.write("Test")
            os.remove(test_file)
        except Exception as e:
            logger.error(f"Cannot write to conversations directory: {str(e)}")
            # If we can't write to the directory, log it but don't fail
            return False
        
        # Write the actual conversation file
        try:
            async with aiofiles.open(file_path, "w") as f:
                await f.write(json.dumps({
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat(),
                    "messages": messages
                }, indent=2))
                logger.info(f"Successfully saved conversation for session: {session_id}")
                return True
        except Exception as e:
            logger.error(f"Error saving conversation file: {str(e)}")
            # Use fallback synchronous write if async fails
            try:
                with open(file_path, "w") as f:
                    f.write(json.dumps({
                        "session_id": session_id,
                        "timestamp": datetime.now().isoformat(),
                        "messages": messages
                    }, indent=2))
                logger.info(f"Saved conversation using synchronous fallback: {session_id}")
                return True
            except Exception as e2:
                logger.error(f"Synchronous fallback also failed: {str(e2)}")
                return False
    except Exception as e:
        logger.error(f"Unexpected error in save_conversation: {str(e)}")
        return False

async def load_conversation(session_id: str) -> List[Dict[str, str]]:
    """Load conversation from a JSON file"""
    file_path = os.path.join(CONVERSATIONS_FOLDER, f"{session_id}.json")
    
    try:
        async with aiofiles.open(file_path, "r") as f:
            content = await f.read()
            data = json.loads(content)
            return data.get("messages", [])
    except FileNotFoundError:
        return []

async def generate_chat_response(messages: List[Dict[str, str]]) -> str:
    """Generate response using OpenAI API"""
    try:
        # Ensure the first message is the system prompt
        if not messages or messages[0]["role"] != "system":
            messages.insert(0, {"role": "system", "content": ELEGANCE_SYSTEM_PROMPT})
        
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.7,
            max_tokens=800,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0
        )
        
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error generating chat response: {str(e)}")
        return "Je suis désolé, mon chéri! I'm having trouble connecting to my fashion knowledge. Please try again in a moment."

async def is_fashion_related(message: str) -> bool:
    """
    Determine if a message is fashion-related.
    Returns True if fashion-related, False otherwise.
    """
    message = message.lower()
    
    # Check for non-fashion topics
    for topic in NON_FASHION_TOPICS:
        if re.search(r'\b' + re.escape(topic) + r'\b', message):
            logging.info(f"Non-fashion topic detected: {topic}")
            return False
    
    # If it's a very short message or greeting, assume it's okay
    if len(message.split()) < 3 or any(greeting in message for greeting in ['hello', 'hi', 'hey', 'bonjour']):
        return True
    
    # Check for fashion keywords
    for keyword in FASHION_KEYWORDS:
        if re.search(r'\b' + re.escape(keyword) + r'\b', message):
            return True
    
    # If no fashion keyword found and message is longer than a greeting, it's likely non-fashion
    return False

async def generate_fashion_redirect() -> str:
    """Generate a polite redirection to fashion topics"""
    redirects = [
        "Ah, mon chéri! While that's an interesting question, I'm here to be your fashion guide! Let's talk about style instead. Perhaps you're curious about current trends or need outfit advice?",
        "Pardonnez-moi, but my expertise is in the world of fashion! I'd be delighted to discuss color theory, styling, or the history of haute couture with you instead.",
        "Fashion is my passion and my purpose! I'd be happy to help you with style advice, color coordination, or any fashion-related questions you might have.",
        "Oh la la! I must redirect our conversation back to the realm of fashion, where I can truly shine. May I suggest discussing your style preferences or a fashion dilemma you're facing?",
        "As Elegance, I'm here exclusively to discuss fashion and style matters. Let me know how I can assist with your fashion needs!"
    ]
    import random
    return random.choice(redirects)

# API endpoints
@app.get("/", response_class=HTMLResponse)
async def home():
    """Simple HTML page with chat interface"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Elegance - Fashion Advisor Chatbot</title>
        <style>
            body {
                font-family: 'Playfair Display', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f8f5f2;
                color: #333;
            }
            h1 {
                color: #b76e79;
                text-align: center;
                margin-bottom: 30px;
                font-style: italic;
            }
            .chat-container {
                display: flex;
                flex-direction: column;
                height: 70vh;
                border: 1px solid #ddd;
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 3px 10px rgba(0,0,0,0.1);
                background-color: white;
            }
            .chat-messages {
                flex: 1;
                overflow-y: auto;
                padding: 20px;
                display: flex;
                flex-direction: column;
            }
            .message {
                margin-bottom: 15px;
                padding: 10px 15px;
                border-radius: 20px;
                max-width: 80%;
                word-wrap: break-word;
            }
            .user-message {
                align-self: flex-end;
                background-color: #e9ebf8;
                color: #333;
                border-bottom-right-radius: 5px;
            }
            .bot-message {
                align-self: flex-start;
                background-color: #f8e2e6;
                color: #333;
                border-bottom-left-radius: 5px;
            }
            .chat-input {
                display: flex;
                padding: 15px;
                border-top: 1px solid #ddd;
                background-color: #f9f9f9;
            }
            #message-input {
                flex: 1;
                padding: 12px;
                border: 1px solid #ddd;
                border-radius: 20px;
                margin-right: 10px;
                font-size: 16px;
            }
            #send-button {
                background: #b76e79;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 20px;
                cursor: pointer;
                font-weight: 500;
                font-size: 16px;
                transition: all 0.3s ease;
            }
            #send-button:hover {
                background: #9a5c65;
                box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            }
            .loading {
                display: none;
                align-self: flex-start;
                font-style: italic;
                color: #999;
                margin-bottom: 15px;
            }
            .signature {
                text-align: center;
                margin-top: 20px;
                font-style: italic;
                color: #888;
            }
        </style>
        <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&display=swap">
    </head>
    <body>
        <h1>Elegance - Votre Conseiller de Mode</h1>
        <div class="chat-container">
            <div class="chat-messages" id="chat-messages">
                <div class="message bot-message">
                    Bonjour, mon chéri! I am Elegance, your personal fashion advisor. How may I assist you with your style today?
                </div>
                <div class="loading" id="loading">Elegance is thinking...</div>
            </div>
            <div class="chat-input">
                <input type="text" id="message-input" placeholder="Ask me about fashion or styling advice...">
                <button id="send-button">Send</button>
            </div>
        </div>
        <div class="signature">~ Elegance, Paris</div>

        <script>
            // Store the session ID
            let sessionId = localStorage.getItem('eleganceSessionId') || generateSessionId();
            localStorage.setItem('eleganceSessionId', sessionId);
            
            // Generate a random session ID
            function generateSessionId() {
                return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
                    var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
                    return v.toString(16);
                });
            }

            // Get DOM elements
            const chatMessages = document.getElementById('chat-messages');
            const messageInput = document.getElementById('message-input');
            const sendButton = document.getElementById('send-button');
            const loadingIndicator = document.getElementById('loading');

            // Send message when clicking the send button
            sendButton.addEventListener('click', sendMessage);

            // Send message when pressing Enter in the input field
            messageInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    sendMessage();
                }
            });

            // Function to send message
            function sendMessage() {
                const message = messageInput.value.trim();
                if (message) {
                    // Add user message to the chat
                    addMessage('user', message);
                    
                    // Clear input field
                    messageInput.value = '';
                    
                    // Show loading indicator
                    loadingIndicator.style.display = 'block';
                    
                    // Send request to the API
                    fetch('/chat', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            message: message,
                            session_id: sessionId
                        }),
                    })
                    .then(response => response.json())
                    .then(data => {
                        // Hide loading indicator
                        loadingIndicator.style.display = 'none';
                        
                        // Add bot response to the chat
                        addMessage('bot', data.response);
                        
                        // Scroll to the bottom
                        chatMessages.scrollTop = chatMessages.scrollHeight;
                    })
                    .catch(error => {
                        // Hide loading indicator
                        loadingIndicator.style.display = 'none';
                        
                        // Add error message
                        addMessage('bot', 'Je suis désolé! There was an error processing your request. Please try again.');
                        console.error('Error:', error);
                    });
                }
            }

            // Function to add message to the chat
            function addMessage(role, content) {
                const messageElement = document.createElement('div');
                messageElement.classList.add('message');
                messageElement.classList.add(role === 'user' ? 'user-message' : 'bot-message');
                messageElement.textContent = content;
                
                // Insert the message before the loading indicator
                chatMessages.insertBefore(messageElement, loadingIndicator);
                
                // Scroll to the bottom
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
        </script>
    </body>
    </html>
    """

@app.post("/chat")
async def chat(request: Request):
    """Chat endpoint for web interface"""
    # Increment the request counter
    CHAT_REQUESTS.inc()
    
    start_time = time.time()
    try:
        # Parse form data
        form_data = await request.form()
        user_message = form_data.get("message", "")
        session_id = form_data.get("session_id", "")
        
        if not user_message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        # Log received message for debugging
        logger.info(f"Received message: {user_message} with session ID: {session_id}")
        
        # Check if message is fashion-related
        is_fashion = await is_fashion_related(user_message)
        if not is_fashion:
            # Increment rejected non-fashion queries counter
            REJECTED_NON_FASHION_QUERIES.inc()
            
            # Generate a redirect message
            bot_response = await generate_fashion_redirect()
            logger.info(f"Redirecting non-fashion topic with: {bot_response}")
            return {"response": bot_response, "session_id": session_id}
        
        # Load existing conversation
        messages = await load_conversation(session_id)
        
        # If it's a new conversation, add the system prompt
        if not messages:
            messages.append({"role": "system", "content": ELEGANCE_SYSTEM_PROMPT})
        
        # Add user message
        messages.append({"role": "user", "content": user_message})
        
        # Generate response
        logger.info("Generating response...")
        response = await generate_chat_response(messages)
        logger.info(f"Generated response: {response[:50]}...")  # Log first 50 chars of response
        
        # Add assistant response to memory
        messages.append({"role": "assistant", "content": response})
        
        # Try to save conversation but continue even if it fails
        save_success = await save_conversation(session_id, messages)
        if not save_success:
            logger.warning("Failed to save conversation to file, but continuing with in-memory only")
        
        # Record token usage if available
        if hasattr(response, 'usage'):
            MODEL_TOKEN_USAGE.labels(type='prompt').inc(response.usage.prompt_tokens)
            MODEL_TOKEN_USAGE.labels(type='completion').inc(response.usage.completion_tokens)
        
        return {"response": response, "session_id": session_id}
    except Exception as e:
        # Increment error counter
        CHAT_ERRORS.inc()
        
        logger.error(f"Error in chat endpoint: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "response": "Je suis désolé! There was an error processing your request. Please try again."}
        )
    finally:
        # Record processing time
        processing_time = time.time() - start_time
        CHAT_PROCESSING_TIME.observe(processing_time)

@app.post("/api/chat")
async def api_chat(request: ChatRequest):
    """API endpoint for chat interaction"""
    # Increment the request counter
    CHAT_REQUESTS.inc()
    
    start_time = time.time()
    try:
        session_id = request.session_id or str(uuid.uuid4())
        
        # Log request
        logger.info(f"API chat request with session ID: {session_id}")
        
        # Convert Pydantic models to dictionaries
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        
        # Check if the latest user message is fashion-related
        user_messages = [msg for msg in messages if msg["role"] == "user"]
        if user_messages:
            latest_user_message = user_messages[-1]["content"]
            is_fashion = await is_fashion_related(latest_user_message)
            if not is_fashion:
                # Increment rejected non-fashion queries counter
                REJECTED_NON_FASHION_QUERIES.inc()
                
                # Generate a redirect message
                bot_response = await generate_fashion_redirect()
                logger.info(f"API: Redirecting non-fashion topic with: {bot_response}")
                return {"response": bot_response, "session_id": session_id}
        
        # Ensure system prompt is present
        if not messages or messages[0]["role"] != "system":
            messages.insert(0, {"role": "system", "content": ELEGANCE_SYSTEM_PROMPT})
        
        # Generate response
        logger.info("Generating API response...")
        try:
            response = await generate_chat_response(messages)
            logger.info(f"Generated API response: {response[:50]}...")  # Log first 50 chars
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"error": f"Error generating response: {str(e)}", 
                         "response": "Je suis désolé! I'm having trouble connecting to my fashion knowledge. Please try again."}
            )
        
        # Add assistant response to memory
        messages.append({"role": "assistant", "content": response})
        
        # Try to save conversation but continue even if it fails
        save_success = await save_conversation(session_id, messages)
        if not save_success:
            logger.warning("Failed to save API conversation to file, but continuing with in-memory only")
        
        # Record token usage if available
        if hasattr(response, 'usage'):
            MODEL_TOKEN_USAGE.labels(type='prompt').inc(response.usage.prompt_tokens)
            MODEL_TOKEN_USAGE.labels(type='completion').inc(response.usage.completion_tokens)
        
        # Update active sessions gauge
        ACTIVE_SESSIONS.inc()
        
        return {"response": response, "session_id": session_id}
    except Exception as e:
        # Increment error counter
        CHAT_ERRORS.inc()
        
        logger.error(f"Error in api_chat endpoint: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "response": "Je suis désolé! There was an error processing your API request. Please try again."}
        )
    finally:
        # Record processing time
        processing_time = time.time() - start_time
        CHAT_PROCESSING_TIME.observe(processing_time)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test creating OpenAI client to ensure API key is valid
        client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Check if conversations directory exists and is writable
        if not os.path.exists(CONVERSATIONS_FOLDER):
            os.makedirs(CONVERSATIONS_FOLDER, exist_ok=True)
            
        # Write a test file to check permissions
        test_file_path = os.path.join(CONVERSATIONS_FOLDER, "health_check_test.txt")
        try:
            with open(test_file_path, 'w') as f:
                f.write("Health check test")
            os.remove(test_file_path)
        except Exception as e:
            return {"status": "error", "message": f"File system error: {str(e)}"}
        
        return {
            "status": "healthy",
            "service": "elegance-chatbot",
            "timestamp": datetime.now().isoformat(),
            "conversations_folder": CONVERSATIONS_FOLDER,
            "api_key_configured": bool(os.getenv("OPENAI_API_KEY"))
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "service": "elegance-chatbot",
            "error": str(e)
        }

@app.get("/fashion-knowledge")
async def fashion_knowledge():
    """Endpoint to showcase fashion knowledge capabilities"""
    return {
        "fashion_expertise": [
            "Color theory and palette coordination",
            "Body type analysis and flattering silhouettes",
            "Fabric properties and seasonal appropriateness",
            "Pattern mixing and textile coordination",
            "Historical fashion influence on modern styles",
            "Formal and casual dress codes",
            "Accessorizing techniques and jewelry coordination",
            "Capsule wardrobe building",
            "Sustainable fashion practices",
            "Garment care and maintenance"
        ],
        "troubleshooting_capabilities": [
            "Clothing detection issues",
            "Style analysis problems",
            "Virtual try-on functionality",
            "API endpoint usage",
            "Common error resolution"
        ]
    }

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return PlainTextResponse(generate_latest(), media_type="text/plain; version=0.0.4; charset=utf-8")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8005, reload=True) 
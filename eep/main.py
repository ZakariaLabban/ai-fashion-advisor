import os
import io
import time
import logging
import base64
import uuid
from datetime import datetime
import asyncio
import numpy as np
import cv2
from fastapi import FastAPI, UploadFile, File, HTTPException, Form, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse, RedirectResponse, StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
import httpx
from PIL import Image
import aiofiles
import json
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Fashion Analysis EEP",
    description="Ensemble Execution Processor for clothing analysis",
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

# Service URLs from environment variables
DETECTION_SERVICE_URL = os.getenv("DETECTION_SERVICE_URL", "http://detection-iep:8001")
STYLE_SERVICE_URL = os.getenv("STYLE_SERVICE_URL", "http://style-iep:8002")
FEATURE_SERVICE_URL = os.getenv("FEATURE_SERVICE_URL", "http://feature-iep:8003")
VIRTUAL_TRYON_SERVICE_URL = os.getenv("VIRTUAL_TRYON_SERVICE_URL", "http://virtual-tryon-iep:8004")
ELEGANCE_SERVICE_URL = os.getenv("ELEGANCE_SERVICE_URL", "http://elegance-iep:8005")
RECO_DATA_SERVICE_URL = os.getenv("RECO_DATA_SERVICE_URL", "http://reco-data-iep:8007")
MATCH_SERVICE_URL = os.getenv("MATCH_SERVICE_URL", "http://match-iep:8008")
TEXT2IMAGE_SERVICE_URL = os.getenv("TEXT2IMAGE_SERVICE_URL", "http://text2image-iep:8020")

# Timeout for service requests (in seconds)
SERVICE_TIMEOUT = int(os.getenv("SERVICE_TIMEOUT", "30"))

# Static folders for file storage
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "/app/static/uploads")
RESULTS_FOLDER = os.getenv("RESULTS_FOLDER", "/app/static/results")

# Ensure folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="/app/static"), name="static")

# Pydantic models for responses
class DetectionInfo(BaseModel):
    class_name: str
    class_id: int
    confidence: float
    bbox: List[int]
    crop_path: Optional[str] = None
    features: Optional[List[float]] = None
    color_histogram: Optional[List[float]] = None

class StyleInfo(BaseModel):
    style_name: str
    style_id: int
    confidence: float

class AnalysisResponse(BaseModel):
    request_id: str
    original_image_path: str
    annotated_image_path: Optional[str] = None
    detections: List[DetectionInfo]
    styles: List[StyleInfo]
    processing_time: float
    timestamp: str

class RecommendationRequest(BaseModel):
    request_id: str
    detection_id: str
    gender: Optional[str] = None
    style: Optional[str] = None
    item_type: str  # "topwear" or "bottomwear"
    operation: str  # "matching" or "similarity"
    
# In-memory store for analysis results
analysis_results_store = {}

@app.get("/", response_class=HTMLResponse)
async def home():
    """Simple HTML page with upload form"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Fashion Analysis System</title>
        <style>
            body { 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                max-width: 1000px; 
                margin: 0 auto; 
                padding: 20px;
                background-color: #f9f9f9;
                color: #333;
            }
            h1 { 
                color: #2c3e50; 
                text-align: center;
                margin-bottom: 30px;
            }
            h2 {
                color: #3498db;
                margin-bottom: 20px;
            }
            form { 
                margin: 20px 0; 
                padding: 25px; 
                border: 1px solid #ddd; 
                border-radius: 8px;
                background-color: white;
                box-shadow: 0 3px 10px rgba(0,0,0,0.1);
            }
            label {
                font-weight: 500;
                display: block;
                margin-bottom: 8px;
                color: #555;
            }
            input, select, button { margin: 10px 0; }
            button { 
                background: #3498db; 
                color: white; 
                padding: 12px 20px; 
                border: none; 
                cursor: pointer;
                border-radius: 5px;
                font-weight: 500;
                font-size: 16px;
                transition: all 0.3s ease;
                width: 100%;
                margin-top: 20px;
            }
            button:hover { 
                background: #2980b9; 
                box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            }
            .form-group {
                margin-bottom: 20px;
            }
            .file-input {
                display: block;
                width: 100%;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
                box-sizing: border-box;
                background-color: #f8f8f8;
            }
            .file-input:hover {
                border-color: #3498db;
            }
            .tabs {
                display: flex;
                margin-bottom: 20px;
                border-bottom: 1px solid #ddd;
            }
            .tab {
                padding: 12px 25px;
                background-color: #f1f1f1;
                cursor: pointer;
                border: 1px solid #ddd;
                border-bottom: none;
                border-radius: 5px 5px 0 0;
                margin-right: 5px;
                font-weight: 500;
                transition: all 0.2s ease;
            }
            .tab:hover {
                background-color: #e0e0e0;
            }
            .tab.active {
                background-color: white;
                border-bottom: 2px solid white;
                color: #3498db;
                margin-bottom: -1px;
            }
            .tab-content {
                display: none;
            }
            .tab-content.active {
                display: block;
            }
            .option-row {
                display: flex;
                gap: 20px;
                margin-bottom: 15px;
            }
            .option-row > div {
                flex: 1;
            }
            .info-text {
                font-size: 14px;
                color: #777;
                margin-top: 5px;
            }
            footer {
                margin-top: 50px;
                text-align: center;
                font-size: 14px;
                color: #888;
                padding-top: 20px;
                border-top: 1px solid #eee;
            }
            /* Chatbot styles */
            .chat-container {
                display: flex;
                flex-direction: column;
                height: 500px;
                border: 1px solid #ddd;
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 3px 10px rgba(0,0,0,0.1);
                background-color: white;
                margin-bottom: 20px;
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
                width: auto;
                margin-top: 0;
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
                text-align: right;
                font-style: italic;
                color: #888;
                padding: 10px;
            }
        </style>
        <script>
            function showTab(tabName) {
                // Hide all tab content
                var tabContents = document.getElementsByClassName('tab-content');
                for (var i = 0; i < tabContents.length; i++) {
                    tabContents[i].style.display = 'none';
                }
                
                // Remove active class from all tabs
                var tabs = document.getElementsByClassName('tab');
                for (var i = 0; i < tabs.length; i++) {
                    tabs[i].className = tabs[i].className.replace(' active', '');
                }
                
                // Show selected tab content and mark tab as active
                document.getElementById(tabName + '-content').style.display = 'block';
                event.currentTarget.className += ' active';
            }
            
            // Initialize the first tab as active when page loads
            document.addEventListener('DOMContentLoaded', function() {
                // Show the analysis tab by default
                document.getElementById('analysis-content').style.display = 'block';
                
                // Setup Elegance chatbot functionality
                setupChatbot();
            });
            
            // Setup Elegance chatbot functionality
            function setupChatbot() {
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
                        fetch('/api/elegance/chat', {
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
            }
        </script>
    </head>
    <body>
        <h1>Fashion Analysis System</h1>
        
        <div class="tabs">
            <div class="tab active" onclick="showTab('analysis')">Clothing Analysis</div>
            <div class="tab" onclick="showTab('tryon')">Virtual Try-On</div>
            <div class="tab" onclick="showTab('multi-tryon')">Multi-Garment Try-On</div>
            <div class="tab" onclick="showTab('match')">Outfit Matcher</div>
            <div class="tab" onclick="showTab('elegance')">Elegance Advisor</div>
            <div class="tab" onclick="showTab('text2image')">Fashion Finder</div>
        </div>

        <div class="tab-content active" id="analysis-content">
            <h2>Upload Image for Clothing Analysis</h2>
            <form action="/analyze" method="post" enctype="multipart/form-data">
                <div class="form-group">
                    <label for="file">Select an image containing clothing items:</label>
                    <input type="file" name="file" id="file" accept="image/*" class="file-input" required>
                </div>
                <button type="submit">Analyze Clothing</button>
            </form>
        </div>

        <div class="tab-content" id="tryon-content">
            <h2>Virtual Try-On</h2>
            <form action="/tryon" method="post" enctype="multipart/form-data">
                <div class="form-group">
                    <label for="model_image">Upload Model Image (Person):</label>
                    <input type="file" name="model_image" id="model_image" accept="image/*" class="file-input" required>
                </div>
                <div class="form-group">
                    <label for="garment_image">Upload Garment Image:</label>
                    <input type="file" name="garment_image" id="garment_image" accept="image/*" class="file-input" required>
                </div>
                <div class="option-row">
                    <div>
                        <label for="category">Garment Category:</label>
                        <select name="category" id="category" class="file-input">
                            <option value="auto">Auto-detect</option>
                            <option value="top">Top / Upper Body</option>
                            <option value="bottom">Bottom / Lower Body</option>
                            <option value="dress">Full Dress</option>
                        </select>
                    </div>
                    <div>
                        <label for="mode">Processing Mode:</label>
                        <select name="mode" id="mode" class="file-input">
                            <option value="quality">High Quality (Slower)</option>
                            <option value="fast">Fast (Lower Quality)</option>
                        </select>
                    </div>
                </div>
                <button type="submit">Try On Garment</button>
            </form>
        </div>

        <div class="tab-content" id="multi-tryon-content">
            <h2>Multi-Garment Try-On</h2>
            <form action="/tryon/multi" method="post" enctype="multipart/form-data">
                <div class="form-group">
                    <label for="model_image_multi">Upload Model Image (Person):</label>
                    <input type="file" name="model_image" id="model_image_multi" accept="image/*" class="file-input" required>
                </div>
                <div class="form-group">
                    <label for="top_image">Upload Top Garment (Optional):</label>
                    <input type="file" name="top_image" id="top_image" accept="image/*" class="file-input">
                    <div class="info-text">Upper body garment (shirt, blouse, jacket, etc.)</div>
                </div>
                <div class="form-group">
                    <label for="bottom_image">Upload Bottom Garment (Optional):</label>
                    <input type="file" name="bottom_image" id="bottom_image" accept="image/*" class="file-input">
                    <div class="info-text">Lower body garment (pants, skirt, shorts, etc.)</div>
                </div>
                <div class="form-group">
                    <div>
                        <label for="mode_multi">Processing Mode:</label>
                        <select name="mode" id="mode_multi" class="file-input">
                            <option value="quality">High Quality (Slower)</option>
                            <option value="fast">Fast (Lower Quality)</option>
                        </select>
                    </div>
                </div>
                <div class="info-text" style="margin-bottom: 20px;">At least one garment (top or bottom) must be provided</div>
                <button type="submit">Try On Multiple Garments</button>
            </form>
        </div>

        <div class="tab-content" id="match-content">
            <h2>Outfit Matcher</h2>
            <p class="info-text">Upload a topwear item and a bottomwear item to check how well they match together.</p>
            <form action="/match" method="post" enctype="multipart/form-data">
                <div class="form-group">
                    <label for="topwear">Upload Topwear Item:</label>
                    <input type="file" name="topwear" id="topwear" accept="image/*" class="file-input" required>
                    <div class="info-text">Shirt, t-shirt, blouse, jacket, etc.</div>
                </div>
                <div class="form-group">
                    <label for="bottomwear">Upload Bottomwear Item:</label>
                    <input type="file" name="bottomwear" id="bottomwear" accept="image/*" class="file-input" required>
                    <div class="info-text">Pants, skirt, shorts, etc.</div>
                </div>
                <button type="submit">Analyze Match</button>
            </form>
        </div>
        
        <div class="tab-content" id="elegance-content">
            <h2>Elegance - Fashion Advisor</h2>
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
        </div>
        
        <div class="tab-content" id="text2image-content">
            <h2>Fashion Finder - Text to Image Search</h2>
            <p class="info-text">Describe the clothing item you're looking for, and we'll find matching images for you.</p>
            <div id="text2image-form-container">
                <div class="form-group">
                    <label for="text-query">What are you looking for?</label>
                    <input type="text" id="text-query" placeholder="e.g., blue floral summer dress, vintage leather jacket, etc." class="file-input">
                </div>
                <button id="search-button" type="button">Find Fashion</button>
            </div>
            <div id="text2image-result" style="margin-top: 30px; text-align: center; display: none;">
                <h3>Search Result</h3>
                <div id="result-image-container" style="margin: 20px auto; max-width: 500px;">
                    <img id="result-image" style="max-width: 100%; border-radius: 8px; box-shadow: 0 3px 10px rgba(0,0,0,0.1);" alt="Fashion Item">
                </div>
                <p id="no-results-message" style="display: none; color: #e74c3c; font-style: italic;">No matching fashion items found. Please try a different search.</p>
            </div>
            <script>
                document.addEventListener('DOMContentLoaded', function() {
                    const searchButton = document.getElementById('search-button');
                    const textQuery = document.getElementById('text-query');
                    const resultContainer = document.getElementById('text2image-result');
                    const resultImage = document.getElementById('result-image');
                    const noResultsMessage = document.getElementById('no-results-message');
                    
                    searchButton.addEventListener('click', function() {
                        const query = textQuery.value.trim();
                        if (!query) {
                            alert('Please enter a search query');
                            return;
                        }
                        
                        // Show loading state
                        searchButton.disabled = true;
                        searchButton.textContent = 'Searching...';
                        resultContainer.style.display = 'none';
                        noResultsMessage.style.display = 'none';
                        
                        // Send request to API
                        fetch('/text2image', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({ query: query }),
                        })
                        .then(response => {
                            searchButton.disabled = false;
                            searchButton.textContent = 'Find Fashion';
                            
                            if (!response.ok) {
                                throw new Error('Search failed');
                            }
                            
                            if (response.headers.get('content-type').includes('image')) {
                                return response.blob();
                            } else {
                                throw new Error('No results found');
                            }
                        })
                        .then(imageBlob => {
                            // Display the image
                            resultImage.src = URL.createObjectURL(imageBlob);
                            resultContainer.style.display = 'block';
                            noResultsMessage.style.display = 'none';
                        })
                        .catch(error => {
                            console.error('Error:', error);
                            resultContainer.style.display = 'block';
                            noResultsMessage.style.display = 'block';
                            resultImage.style.display = 'none';
                        });
                    });
                    
                    // Also trigger search on Enter key
                    textQuery.addEventListener('keypress', function(e) {
                        if (e.key === 'Enter') {
                            searchButton.click();
                        }
                    });
                });
            </script>
        </div>
        
        <footer>
            <p>Fashion Analysis System &copy; 2024 | For more information, visit our <a href="/docs">API Documentation</a></p>
        </footer>
    </body>
    </html>
    """

@app.get("/health")
async def health_check():
    """Health check for the EEP service"""
    return {"status": "healthy", "service": "Fashion Analysis EEP"}

@app.get("/api/analyze/health")
async def analyze_health_check():
    """Health check specifically for the analyze feature"""
    return {
        "status": "healthy", 
        "service": "Fashion Analysis EEP",
        "feature": "analyze",
        "endpoints": ["/api/analyze", "/analyze"]
    }

async def check_iep_health(client: httpx.AsyncClient, service_url: str, service_name: str) -> bool:
    """Check health of an IEP service"""
    try:
        response = await client.get(f"{service_url}/health", timeout=5.0)
        if response.status_code == 200:
            return True
        logger.warning(f"{service_name} health check failed with status {response.status_code}")
        return False
    except Exception as e:
        logger.warning(f"{service_name} health check failed: {e}")
        return False

@app.get("/services/health")
async def check_services_health():
    """Check the health of all dependent services"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            tasks = [
                check_iep_health(client, f"{DETECTION_SERVICE_URL}/health", "Detection IEP"),
                check_iep_health(client, f"{STYLE_SERVICE_URL}/health", "Style IEP"),
                check_iep_health(client, f"{FEATURE_SERVICE_URL}/health", "Feature IEP"),
                check_iep_health(client, f"{VIRTUAL_TRYON_SERVICE_URL}/health", "Virtual Try-On IEP"),
                check_iep_health(client, f"{ELEGANCE_SERVICE_URL}/health", "Elegance Chatbot IEP"),
                check_iep_health(client, f"{RECO_DATA_SERVICE_URL}/health", "Recommendation Data IEP"),
                check_iep_health(client, f"{MATCH_SERVICE_URL}/health", "Match Analysis IEP"),
                check_iep_health(client, f"{TEXT2IMAGE_SERVICE_URL}/health", "Text to Image IEP"),
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            services_status = {
                "detection": str(results[0] == True),
                "style": str(results[1] == True),
                "feature": str(results[2] == True),
                "virtual_tryon": str(results[3] == True),
                "elegance": str(results[4] == True),
                "reco_data": str(results[5] == True),
                "match": str(results[6] == True),
                "text2image": str(results[7] == True),
            }
            
            all_healthy = all(s == "True" for s in services_status.values())
            
            return {
                "status": "healthy" if all_healthy else "degraded",
                "services": services_status
            }
    except Exception as e:
        logger.error(f"Error checking service health: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

async def save_uploaded_image(file_contents: bytes, filename: str) -> str:
    """Save uploaded image to disk and return path"""
    # Use the exact filename that was passed in
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    
    # Save the file
    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(file_contents)
    
    return file_path

async def annotate_image(image_path: str, detections: List[Any]) -> str:
    """Annotate the original image with detection bounding boxes"""
    try:
        # Read the image
        img = cv2.imread(image_path)
        if img is None:
            logger.error(f"Could not read image: {image_path}")
            # Return just the original image path
            base_name = os.path.basename(image_path)
            return f"/static/uploads/{base_name}"
            
        # Create filename for the annotated image (always use jpg extension)
        base_name = os.path.basename(image_path)
        file_name_without_ext = os.path.splitext(base_name)[0]
        annotated_filename = f"{file_name_without_ext}_annotated.jpg"
        
        # Save directly to the results folder (not in a subdirectory)
        annotated_path = os.path.join(RESULTS_FOLDER, annotated_filename)
        
        # Draw bounding boxes
        for detection in detections:
            # Handle both Dict and DetectionInfo objects
            if isinstance(detection, dict):
                bbox = detection["bbox"]
                label = detection["class_name"]
                conf = detection["confidence"]
            else:
                # DetectionInfo object
                bbox = detection.bbox
                label = detection.class_name
                conf = detection.confidence
            
            # Convert to integers
            x1, y1, x2, y2 = map(int, bbox)
            
            # Draw the box
            color = (0, 255, 0)  # Green
            thickness = 2
            cv2.rectangle(img, (x1, y1), (x2, y2), color, thickness)
            
            # Add label
            text = f"{label}: {conf:.2f}"
            font_scale = 0.5
            font_thickness = 1
            text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, font_thickness)[0]
            
            # Ensure label background stays within image
            text_y = max(y1, text_size[1] + 10)
            
            # Draw background rectangle for text
            cv2.rectangle(img, (x1, text_y - text_size[1] - 10), (x1 + text_size[0], text_y), (255, 255, 255), -1)
            
            # Draw text
            cv2.putText(img, text, (x1, text_y - 5), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 0, 0), font_thickness)
        
        # Save the annotated image
        cv2.imwrite(annotated_path, img)
        
        # Return just the filename instead of the full path
        return f"/static/results/{annotated_filename}"
        
    except Exception as e:
        logger.error(f"Error annotating image: {str(e)}")
        logger.error(traceback.format_exc())
        # If annotation fails, return the original image path
        base_name = os.path.basename(image_path)
        return f"/static/uploads/{base_name}"

async def process_detection(client: httpx.AsyncClient, image_data: bytes, request_id: str) -> List[Dict]:
    """Call detection IEP to detect clothing items"""
    try:
        logger.info(f"[{request_id}] Sending request to Detection IEP")
        files = {'file': ('image.jpg', image_data, 'image/jpeg')}
        data = {'include_crops': True}
        
        response = await client.post(
            f"{DETECTION_SERVICE_URL}/detect",
            files=files,
            data=data,
            timeout=SERVICE_TIMEOUT
        )
        
        if response.status_code != 200:
            logger.error(f"[{request_id}] Detection IEP error: {response.status_code} - {response.text}")
            raise HTTPException(status_code=response.status_code, detail="Detection service error")
        
        result = response.json()
        logger.info(f"[{request_id}] Detection found {len(result['detections'])} items")
        return result['detections']
    except httpx.TimeoutException:
        logger.error(f"[{request_id}] Detection IEP timeout after {SERVICE_TIMEOUT}s")
        raise HTTPException(status_code=504, detail="Detection service timeout")
    except Exception as e:
        logger.error(f"[{request_id}] Detection IEP error: {e}")
        raise HTTPException(status_code=500, detail=f"Detection error: {str(e)}")

async def process_style(client: httpx.AsyncClient, image_data: bytes, request_id: str) -> List[Dict]:
    """Call style IEP to classify clothing style"""
    try:
        logger.info(f"[{request_id}] Sending request to Style IEP")
        files = {'file': ('image.jpg', image_data, 'image/jpeg')}
        
        response = await client.post(
            f"{STYLE_SERVICE_URL}/classify",
            files=files,
            timeout=SERVICE_TIMEOUT
        )
        
        if response.status_code != 200:
            logger.error(f"[{request_id}] Style IEP error: {response.status_code} - {response.text}")
            raise HTTPException(status_code=response.status_code, detail="Style service error")
        
        result = response.json()
        logger.info(f"[{request_id}] Style classification found {len(result['styles'])} styles")
        return result['styles']
    except httpx.TimeoutException:
        logger.error(f"[{request_id}] Style IEP timeout after {SERVICE_TIMEOUT}s")
        raise HTTPException(status_code=504, detail="Style service timeout")
    except Exception as e:
        logger.error(f"[{request_id}] Style IEP error: {e}")
        raise HTTPException(status_code=500, detail=f"Style error: {str(e)}")

async def process_feature_extraction(client: httpx.AsyncClient, crop_data: bytes, request_id: str, item_index: int) -> Dict:
    """Call feature IEP to extract features from a clothing item crop"""
    try:
        logger.info(f"[{request_id}] Sending crop {item_index} to Feature IEP")
        files = {'file': (f'crop_{item_index}.jpg', crop_data, 'image/jpeg')}
        
        response = await client.post(
            f"{FEATURE_SERVICE_URL}/extract",
            files=files,
            timeout=SERVICE_TIMEOUT
        )
        
        if response.status_code != 200:
            logger.error(f"[{request_id}] Feature IEP error for crop {item_index}: {response.status_code} - {response.text}")
            raise HTTPException(status_code=response.status_code, detail="Feature extraction service error")
        
        return response.json()
    except httpx.TimeoutException:
        logger.error(f"[{request_id}] Feature IEP timeout for crop {item_index} after {SERVICE_TIMEOUT}s")
        raise HTTPException(status_code=504, detail="Feature extraction service timeout")
    except Exception as e:
        logger.error(f"[{request_id}] Feature IEP error for crop {item_index}: {e}")
        raise HTTPException(status_code=500, detail=f"Feature extraction error: {str(e)}")

async def process_recommendation(client: httpx.AsyncClient, vector: List[float], gender: Optional[str], 
                               style: Optional[str], item_type: str, operation: str) -> bytes:
    """
    Process a recommendation request to the Recommendation IEP.
    Returns the image as bytes.
    """
    start_time = time.time()
    
    # Build query params
    params = {}
    if gender:
        params["gender"] = gender
    if style:
        params["style"] = style
    if item_type:
        params["type_"] = item_type
        
    # Build request body - send vector directly instead of in an object
    data = vector  # Modified: Sending the vector directly instead of {"vector": vector}
    
    # Select the correct endpoint based on operation
    endpoint = "matching" if operation == "matching" else "similarity"
    
    try:
        # Log the request details
        logger.info(f"Sending recommendation request to {RECO_DATA_SERVICE_URL}/{endpoint}")
        logger.info(f"Parameters: {params}")
        logger.info(f"Vector length: {len(vector)}")
        
        # Make the request to the recommendation service
        response = await client.post(
            f"{RECO_DATA_SERVICE_URL}/{endpoint}",
            params=params,
            json=data,
            timeout=SERVICE_TIMEOUT
        )
        
        if response.status_code != 200:
            error_detail = response.text
            try:
                error_json = response.json()
                if "detail" in error_json:
                    error_detail = error_json["detail"]
            except:
                pass
                
            logger.error(f"Recommendation service error: {response.status_code}, {error_detail}")
            raise HTTPException(status_code=response.status_code, 
                              detail=f"Recommendation service error: {error_detail}")
        
        # Return the image bytes directly
        logger.info(f"Recommendation request successful, received {len(response.content)} bytes")
        return response.content
        
    except httpx.HTTPError as e:
        logger.error(f"HTTP error processing recommendation: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Error connecting to recommendation service: {str(e)}")
    except httpx.TimeoutException:
        logger.error(f"Timeout contacting recommendation service after {SERVICE_TIMEOUT} seconds")
        raise HTTPException(status_code=504, detail=f"Recommendation service timeout after {SERVICE_TIMEOUT} seconds")
    except Exception as e:
        logger.error(f"Error processing recommendation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing recommendation: {str(e)}")
    finally:
        logger.info(f"Recommendation processing took {time.time() - start_time:.2f} seconds")

async def save_crop_image(crop_data_b64: str, class_name: str, item_index: int, request_id: str) -> str:
    """Save a base64 encoded crop image to disk and return path"""
    try:
        # Decode base64 data
        crop_data = base64.b64decode(crop_data_b64)
        
        # Generate a unique filename
        file_extension = ".jpg"
        safe_filename = f"{request_id}_{class_name.replace('/', '_')}_{item_index}{file_extension}"
        
        # Create full path
        file_path = os.path.join(RESULTS_FOLDER, safe_filename)
        
        # Save the file
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(crop_data)
        
        return f"/static/results/{safe_filename}"
    except Exception as e:
        logger.error(f"Error saving crop image: {e}")
        return None

@app.post("/analyze")
async def analyze_image(request: Request, file: UploadFile = File(...)):
    """
    Analyze clothing in an uploaded image.
    
    This endpoint:
    1. Detects clothing items using the detection IEP
    2. Classifies style using the style IEP
    3. Extracts features from each detected item using the feature IEP
    """
    # Generate request ID
    request_id = str(uuid.uuid4())
    logger.info(f"[{request_id}] Starting analysis for file: {file.filename}")
    
    start_time = time.time()
    
    try:
        # Read uploaded file
        contents = await file.read()
        
        # Save the original image
        image_path = await save_uploaded_image(contents, file.filename)
        relative_image_path = f"/static/uploads/{os.path.basename(image_path)}"
        
        async with httpx.AsyncClient() as client:
            # 1. Call detection IEP
            try:
                detections_raw = await process_detection(client, contents, request_id)
            except Exception as e:
                logger.error(f"[{request_id}] Detection error: {str(e)}")
                # For API calls, return JSON error
                if "application/json" in request.headers.get("content-type", ""):
                    return JSONResponse(
                        status_code=500,
                        content={"error": "Detection service error", "detail": str(e)}
                    )
                # For web requests, raise HTTPException which will be caught in outer try/except
                raise e
            
            # 2. Call style IEP (in parallel with feature extraction)
            style_task = asyncio.create_task(process_style(client, contents, request_id))
            
            # 3. Process each detection to extract features
            detections = []
            feature_tasks = []
            
            for i, det in enumerate(detections_raw):
                # Save crop image if available
                crop_path = None
                if det.get('crop_data'):
                    crop_path = await save_crop_image(
                        det['crop_data'], 
                        det['class_name'], 
                        i, 
                        request_id
                    )
                    
                    # Create task for feature extraction from the crop
                    crop_data = base64.b64decode(det['crop_data'])
                    task = process_feature_extraction(client, crop_data, request_id, i)
                    feature_tasks.append((i, task))
                
                # Create detection info (without features yet)
                detection = DetectionInfo(
                    class_name=det['class_name'],
                    class_id=det['class_id'],
                    confidence=det['confidence'],
                    bbox=det['bbox'],
                    crop_path=crop_path
                )
                detections.append(detection)
            
            # 4. Wait for style results
            try:
                styles_raw = await style_task
                styles = [StyleInfo(**style) for style in styles_raw]
            except Exception as e:
                logger.error(f"[{request_id}] Style classification error: {str(e)}")
                # Use a default empty style list
                styles = []
                # For API calls, don't fail completely, just log and continue
                if "application/json" in request.headers.get("content-type", ""):
                    logger.warning(f"[{request_id}] Continuing with empty style list")
                else:
                    # For web requests, raise the exception to show error page
                    raise e
            
            # 5. Wait for all feature extraction tasks and add results to detections
            for i, task in feature_tasks:
                try:
                    features_result = await task
                    detections[i].features = features_result['features']
                    detections[i].color_histogram = features_result['color_histogram']
                except Exception as e:
                    logger.error(f"[{request_id}] Failed to extract features for detection {i}: {e}")
                    # Continue without features - don't fail the whole request
            
            # 6. Create annotated image
            annotated_path = await annotate_image(image_path, detections)
            
            # Calculate total processing time
            processing_time = time.time() - start_time
            
            # Determine if it's an API call or web form submission
            content_type = request.headers.get("content-type", "")
            
            # Store analysis results for recommendation endpoint
            analysis_data = {
                "request_id": request_id,
                "original_image_path": relative_image_path,
                "annotated_image_path": annotated_path,
                "detections": [d.dict() for d in detections],
                "styles": [s.dict() for s in styles],
                "processing_time": processing_time,
                "timestamp": datetime.now().isoformat()
            }
            analysis_results_store[request_id] = analysis_data
            
            # For API calls, return JSON
            if "application/json" in content_type:
                # Create the response object
                response = AnalysisResponse(
                    request_id=request_id,
                    original_image_path=relative_image_path,
                    annotated_image_path=annotated_path,
                    detections=detections,
                    styles=styles,
                    processing_time=processing_time,
                    timestamp=datetime.now().isoformat()
                )
                
                # Return as a regular dict
                return response
            
            # For web form submissions, generate HTML directly
            html_content = generate_result_html(
                request_id=request_id,
                original_img=relative_image_path,
                annotated_img=annotated_path,
                detections=detections,
                styles=styles,
                processing_time=processing_time,
                timestamp=datetime.now().isoformat()
            )
            
            return HTMLResponse(content=html_content)
    
    except Exception as e:
        logger.error(f"[{request_id}] Analysis error: {e}")
        logger.error(traceback.format_exc())
        
        # Determine if it's an API call or web form submission
        content_type = request.headers.get("content-type", "")
        
        # For API calls, return JSON error
        if "application/json" in content_type:
            return JSONResponse(
                status_code=500,
                content={"error": "Analysis error", "detail": str(e)}
            )
        
        # For web form submissions, show error page
        error_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Error</title>
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
                .error-box {{ background-color: #ffebee; padding: 20px; border-radius: 5px; border-left: 5px solid #f44336; }}
                h1 {{ color: #d32f2f; }}
                pre {{ background-color: #f5f5f5; padding: 10px; overflow: auto; }}
                .back-btn {{ background-color: #4CAF50; color: white; padding: 10px 15px; text-decoration: none; display: inline-block; margin-top: 20px; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <h1>Analysis Error</h1>
            <div class="error-box">
                <h2>An error occurred during processing:</h2>
                <p>{str(e)}</p>
                <pre>{traceback.format_exc()}</pre>
            </div>
            <a href="/" class="back-btn">Try Again</a>
        </body>
        </html>
        """
        return HTMLResponse(content=error_html, status_code=500)

@app.post("/api/analyze")
async def api_analyze_image(file: UploadFile = File(...)):
    """API endpoint that always returns JSON"""
    # Generate a request ID for logging
    request_id = str(uuid.uuid4())
    logger.info(f"[{request_id}] API Analyze: Starting analysis for file: {file.filename}")
    
    try:
        # Create a fake request with JSON content type
        fake_headers = [("content-type", "application/json")]
        fake_request = Request(scope={"type": "http", "headers": fake_headers})
        
        # Call the main analyze_image function which will already return a proper response
        result = await analyze_image(fake_request, file)
        
        # Return the result directly - it's already a proper response object
        return result
        
    except Exception as e:
        # Log any unexpected errors
        logger.exception(f"[{request_id}] Unhandled error in api_analyze_image: {str(e)}")
        
        # Return a clean JSON error response
        return JSONResponse(
            status_code=500,
            content={
                "error": "API processing error", 
                "detail": str(e),
                "request_id": request_id
            }
        )

def generate_result_html(request_id, original_img, annotated_img, detections, styles, processing_time, timestamp):
    """Generate HTML for displaying analysis results"""
    
    # Define clothing types that can be used for recommendations
    reco_capable_classes = ["Shirt", "Jumpsuit", "Pants", "Shorts", "Pants/Shorts", "Skirt", "Dress"]
    
    styles_html = ""
    for style in styles:
        confidence_percent = style["confidence"] * 100 if isinstance(style, dict) else style.confidence * 100
        style_name = style["style_name"] if isinstance(style, dict) else style.style_name
        styles_html += f'''
        <div class="style-item">
            <span class="style-name">{style_name}</span>
            <div class="confidence-bar">
                <div class="confidence-fill" style="width: {confidence_percent}%;"></div>
            </div>
            <span class="confidence-value">{confidence_percent:.1f}%</span>
        </div>
        '''
    
    detections_html = ""
    for i, detection in enumerate(detections):
        if isinstance(detection, dict):
            class_name = detection["class_name"]
            confidence = detection["confidence"]
            crop_path = detection.get("crop_path", "")
            features = detection.get("features", [])
            color_histogram = detection.get("color_histogram", [])
        else:
            class_name = detection.class_name
            confidence = detection.confidence
            crop_path = detection.crop_path or ""
            features = detection.features or []
            color_histogram = detection.color_histogram or []
            
        # Truncate features and histogram for display
        features_preview = str(features[:5]) + ("..." if len(features) > 5 else "")
        histogram_preview = str(color_histogram[:5]) + ("..." if len(color_histogram) > 5 else "")
        
        detections_html += f'''
        <div class="detection-box" id="detection-{i}">
            <div class="detection-header">
                <h3>{class_name} (Confidence: {confidence:.2f})</h3>
            </div>
            
            <img src="{crop_path}" alt="{class_name}" class="detection-image">
            
            <div class="features-box">
                <p><strong>Features:</strong></p>
                <div id="features_{i}" class="features-preview">{features_preview}</div>
                <button onclick="toggleFeatures('features_{i}')" class="toggle-btn">Show More</button>
                
                <p><strong>Color Histogram:</strong></p>
                <div id="histogram_{i}" class="histogram-preview">{histogram_preview}</div>
                <button onclick="toggleFeatures('histogram_{i}')" class="toggle-btn">Show More</button>
            </div>
        '''
        
        # Add recommendation buttons for supported garment types
        if class_name in reco_capable_classes:
            item_type = "topwear" if class_name in ["Shirt", "Jumpsuit"] else "bottomwear"
            detections_html += f'''
            <div class="recommendation-options">
                <button id="similar-btn-{i}" class="reco-button" onclick="showRecoOptions('{i}', '{class_name}', '{item_type}')">Find Similar</button>
                <button id="matching-btn-{i}" class="reco-button matching" onclick="showRecoOptions('{i}', '{class_name}', '{item_type}', true)">Find Matching</button>
            </div>
            <div id="reco-modal-{i}" class="reco-modal">
                <div class="reco-modal-content">
                    <span class="reco-close" onclick="closeRecoModal('{i}')">&times;</span>
                    <h3 id="reco-title-{i}">Find Similar Items</h3>
                    
                    <div class="reco-tabs">
                        <button id="similar-tab-{i}" class="reco-tab active" onclick="switchOperation('{i}', false)">Find Similar</button>
                        <button id="matching-tab-{i}" class="reco-tab" onclick="switchOperation('{i}', true)">Find Matching</button>
                    </div>
                    
                    <form id="reco-form-{i}" action="/recommendation" method="post" target="_blank">
                        <input type="hidden" name="request_id" value="{request_id}">
                        <input type="hidden" name="detection_id" value="{i}">
                        <input type="hidden" name="operation" id="operation-{i}" value="similarity">
                        <input type="hidden" name="item_type" id="item-type-{i}" data-original-type="{item_type}" value="{item_type}">
                        <input type="hidden" id="item-class-{i}" value="{class_name}">
                        
                        <div class="reco-form-row">
                            <label for="gender-{i}">Gender:</label>
                            <select name="gender" id="gender-{i}" class="reco-select">
                                <option value="">Any</option>
                                <option value="male">Men</option>
                                <option value="female">Women</option>
                            </select>
                        </div>
                        
                        <div class="reco-form-row">
                            <label for="style-{i}">Style:</label>
                            <select name="style" id="style-{i}" class="reco-select">
                                <option value="">Any</option>
                                <option value="casual">Casual</option>
                                <option value="formal">Formal</option>
                                <option value="athletic wear">Athletic Wear</option>
                                <option value="streetwear">Streetwear</option>
                                <option value="other">Other</option>
                            </select>
                        </div>
                        
                        <button type="submit" id="submit-btn-{i}" class="reco-submit">Find Similar Items</button>
                    </form>
                </div>
            </div>
            '''
        
        detections_html += '</div>'
    
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Fashion Analysis Results</title>
        <style>
            body {{ 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                max-width: 1000px; 
                margin: 0 auto; 
                padding: 20px;
                background-color: #f9f9f9;
                color: #333;
            }}
            .container {{
                padding: 20px;
            }}
            .header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 30px;
            }}
            h1, h2, h3 {{ 
                color: #2c3e50;
            }}
            h1 {{ 
                text-align: center;
                margin-bottom: 30px;
            }}
            .back-btn {{
                display: inline-block;
                padding: 10px 15px;
                background-color: #3498db;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                font-weight: 500;
                transition: all 0.3s ease;
            }}
            .back-btn:hover {{
                background-color: #2980b9;
                box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            }}
            .images-container {{
                display: flex;
                flex-wrap: wrap;
                gap: 20px;
                margin-bottom: 30px;
            }}
            .image-box {{
                flex: 1;
                min-width: 300px;
                background-color: white;
                border-radius: 8px;
                box-shadow: 0 3px 10px rgba(0,0,0,0.1);
                padding: 15px;
                text-align: center;
            }}
            .image-box h3 {{
                margin-top: 0;
                color: #3498db;
            }}
            .image-box img {{
                max-width: 100%;
                max-height: 500px;
                object-fit: contain;
                border-radius: 5px;
                display: block;
                margin: 0 auto;
            }}
            .styles-container {{
                background-color: white;
                border-radius: 8px;
                box-shadow: 0 3px 10px rgba(0,0,0,0.1);
                padding: 20px;
                margin-bottom: 30px;
            }}
            .style-item {{
                display: flex;
                align-items: center;
                margin-bottom: 15px;
            }}
            .style-name {{
                min-width: 150px;
                font-weight: bold;
            }}
            .confidence-bar {{
                flex-grow: 1;
                height: 20px;
                background-color: #eee;
                border-radius: 10px;
                margin: 0 15px;
                overflow: hidden;
            }}
            .confidence-fill {{
                height: 100%;
                background-color: #3498db;
                border-radius: 10px;
            }}
            .confidence-value {{
                min-width: 60px;
                text-align: right;
            }}
            .detections-container {{
                margin-bottom: 30px;
            }}
            .detection-box {{
                background-color: white;
                padding: 20px;
                margin-bottom: 15px;
                border-radius: 8px;
                box-shadow: 0 3px 10px rgba(0,0,0,0.1);
            }}
            .detection-header {{
                display: flex;
                justify-content: space-between;
                margin-bottom: 10px;
            }}
            .detection-image {{
                max-width: 150px;
                max-height: 150px;
                border: 1px solid #ddd;
                margin-right: 15px;
                float: left;
                border-radius: 5px;
            }}
            .features-box {{
                background-color: #f5f5f5;
                padding: 15px;
                border-radius: 5px;
                margin-top: 10px;
                overflow: auto;
                clear: both;
            }}
            .features-preview, .histogram-preview {{
                font-family: monospace;
                white-space: pre-wrap;
                background-color: #f8f8f8;
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 5px;
                margin-top: 5px;
                max-height: 100px;
                overflow-y: auto;
            }}
            .toggle-btn {{
                background-color: #3498db;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 5px;
                cursor: pointer;
                margin-top: 5px;
                font-size: 0.8em;
            }}
            .toggle-btn:hover {{
                background-color: #2980b9;
            }}
            .metadata {{
                font-size: 0.9em;
                color: #666;
                margin-top: 30px;
                padding: 15px;
                border-top: 1px solid #ddd;
                background-color: #f1f1f1;
                border-radius: 5px;
            }}
            
            /* Recommendation styles */
            .recommendation-options {{
                margin-top: 15px;
                display: flex;
                gap: 10px;
            }}
            .reco-button {{
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 12px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 0.9em;
            }}
            .reco-button.matching {{
                background-color: #e74c3c;
            }}
            .reco-button.active, .reco-tab.active {{
                box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.5);
                font-weight: bold;
            }}
            .reco-button:hover {{
                opacity: 0.9;
                box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            }}
            .reco-tabs {{
                display: flex;
                margin-bottom: 15px;
                border-bottom: 1px solid #ddd;
            }}
            .reco-tab {{
                flex: 1;
                background-color: #f8f8f8;
                border: none;
                padding: 10px;
                cursor: pointer;
                transition: all 0.2s;
                border-radius: 5px 5px 0 0;
            }}
            .reco-tab:first-child {{
                background-color: #3498db;
                color: white;
            }}
            .reco-tab:last-child {{
                background-color: #e74c3c;
                color: white;
            }}
            .reco-tab.active {{
                border-bottom: 3px solid #2980b9;
                font-weight: bold;
            }}
            .reco-tab:hover {{
                background-color: #e9e9e9;
            }}
            .reco-tab:first-child:hover {{
                background-color: #2980b9;
            }}
            .reco-tab:last-child:hover {{
                background-color: #c0392b;
            }}
            .reco-modal {{
                display: none;
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(0,0,0,0.5);
                z-index: 1000;
                overflow: auto;
            }}
            .reco-modal-content {{
                background-color: white;
                margin: 10% auto;
                padding: 20px;
                border-radius: 8px;
                width: 80%;
                max-width: 500px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.2);
                position: relative;
            }}
            .reco-close {{
                position: absolute;
                top: 10px;
                right: 15px;
                font-size: 28px;
                font-weight: bold;
                cursor: pointer;
            }}
            .reco-form-row {{
                margin-bottom: 15px;
            }}
            .reco-form-row label {{
                display: block;
                margin-bottom: 5px;
                font-weight: 500;
            }}
            .reco-select {{
                width: 100%;
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }}
            .reco-submit {{
                background-color: #2ecc71;
                color: white;
                border: none;
                padding: 10px 15px;
                border-radius: 5px;
                cursor: pointer;
                font-weight: 500;
                width: 100%;
                margin-top: 10px;
            }}
            .reco-submit:hover {{
                background-color: #27ae60;
            }}
        </style>
        <script>
            function toggleFeatures(id) {{
                const el = document.getElementById(id);
                if (el.style.maxHeight === '100px' || el.style.maxHeight === '') {{
                    el.style.maxHeight = 'none';
                }} else {{
                    el.style.maxHeight = '100px';
                }}
            }}
            
            function showRecoOptions(id, className, itemType, isMatching = false) {{
                // Show the modal
                const modal = document.getElementById(`reco-modal-${{id}}`);
                modal.style.display = 'block';
                
                // Update the title
                const title = document.getElementById(`reco-title-${{id}}`);
                title.textContent = isMatching ? `Find Items to Match with ${{className}}` : `Find Similar ${{className}}s`;
                
                // Set the operation value
                const operationField = document.getElementById(`operation-${{id}}`);
                operationField.value = isMatching ? 'matching' : 'similarity';
                
                // For matching, set appropriate item_type
                if (isMatching) {{
                    const itemTypeField = document.getElementById(`item-type-${{id}}`);
                    itemTypeField.value = itemType === 'topwear' ? 'bottomwear' : 'topwear';
                }} else {{
                    // Make sure item_type is set correctly for similarity
                    const itemTypeField = document.getElementById(`item-type-${{id}}`);
                    itemTypeField.value = itemType;
                }}
                
                // Add visual indicators for mode
                const similarBtn = document.getElementById(`similar-btn-${{id}}`);
                const matchingBtn = document.getElementById(`matching-btn-${{id}}`);
                
                if (isMatching) {{
                    similarBtn.classList.remove('active');
                    matchingBtn.classList.add('active');
                    document.getElementById(`submit-btn-${{id}}`).textContent = 'Find Matching Items';
                }} else {{
                    similarBtn.classList.add('active');
                    matchingBtn.classList.remove('active');
                    document.getElementById(`submit-btn-${{id}}`).textContent = 'Find Similar Items';
                }}
                
                // Update form attributes based on operation
                const form = document.getElementById(`reco-form-${{id}}`);
                form.reset(); // Reset any previous selections
            }}
            
            function closeRecoModal(id) {{
                const modal = document.getElementById(`reco-modal-${{id}}`);
                modal.style.display = 'none';
            }}
            
            function switchOperation(id, isMatching) {{
                // Set the operation value
                const operationField = document.getElementById(`operation-${{id}}`);
                operationField.value = isMatching ? 'matching' : 'similarity';
                
                // Get the item type
                const itemTypeField = document.getElementById(`item-type-${{id}}`);
                const currentType = itemTypeField.getAttribute('data-original-type');
                
                // For matching, set appropriate item_type
                if (isMatching) {{
                    itemTypeField.value = currentType === 'topwear' ? 'bottomwear' : 'topwear';
                }} else {{
                    itemTypeField.value = currentType;
                }}
                
                // Update visual indicators
                const similarBtn = document.getElementById(`similar-btn-${{id}}`);
                const matchingBtn = document.getElementById(`matching-btn-${{id}}`);
                
                if (isMatching) {{
                    similarBtn.classList.remove('active');
                    matchingBtn.classList.add('active');
                    document.getElementById(`submit-btn-${{id}}`).textContent = 'Find Matching Items';
                }} else {{
                    similarBtn.classList.add('active');
                    matchingBtn.classList.remove('active');
                    document.getElementById(`submit-btn-${{id}}`).textContent = 'Find Similar Items';
                }}
                
                // Update the title
                const className = document.getElementById(`item-class-${{id}}`).value;
                const title = document.getElementById(`reco-title-${{id}}`);
                title.textContent = isMatching ? `Find Items to Match with ${{className}}` : `Find Similar ${{className}}s`;
            }}
            
            // Close modal when clicking outside content
            window.onclick = function(event) {{
                if (event.target.className === 'reco-modal') {{
                    event.target.style.display = 'none';
                }}
            }}
        </script>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Fashion Analysis Results</h1>
                <a href="/" class="back-btn">Back to Upload</a>
            </div>
            
            <div class="images-container">
                <div class="image-box">
                    <h3>Original Image</h3>
                    <img src="{original_img}" alt="Original Image">
                </div>
                <div class="image-box">
                    <h3>Annotated Image</h3>
                    <img src="{annotated_img}" alt="Annotated Image" onerror="this.src='{original_img}'; this.title='Annotated image not available'">
                </div>
            </div>
            
            <div class="styles-container">
                <h2>Style Classification</h2>
                {styles_html}
            </div>
            
            <div class="detections-container">
                <h2>Clothing Items Detected ({len(detections)})</h2>
                {detections_html}
            </div>
            
            <div class="metadata">
                <p><strong>Request ID:</strong> {request_id}</p>
                <p><strong>Processing Time:</strong> {processing_time:.2f} seconds</p>
                <p><strong>Timestamp:</strong> {timestamp}</p>
            </div>
        </div>
    </body>
    </html>
    '''
    
    return html

async def process_virtual_tryon(
    client: httpx.AsyncClient,
    model_image_data: str, 
    garment_image_data: str,
    category: str = "auto",
    mode: str = "quality"
) -> Dict:
    """Process virtual try-on request through the Virtual Try-On IEP"""
    try:
        payload = {
            "model_image_data": model_image_data,
            "garment_image_data": garment_image_data,
            "category": category,
            "mode": mode
        }
        
        response = await client.post(
            f"{VIRTUAL_TRYON_SERVICE_URL}/tryon",
            json=payload,
            timeout=float(SERVICE_TIMEOUT)
        )
        
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"Virtual Try-On service returned error: {e.response.text}")
        raise HTTPException(status_code=e.response.status_code, detail=f"Virtual Try-On service error: {e.response.text}")
    except httpx.RequestError as e:
        logger.error(f"Error connecting to Virtual Try-On service: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Virtual Try-On service unavailable: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in Virtual Try-On processing: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Virtual Try-On processing failed: {str(e)}")

async def process_text2image(client: httpx.AsyncClient, query: str) -> bytes:
    """Process text-to-image request through the Text2Image IEP"""
    try:
        payload = {
            "query": query
        }
        
        response = await client.post(
            f"{TEXT2IMAGE_SERVICE_URL}/text-search",
            json=payload,
            timeout=float(SERVICE_TIMEOUT)
        )
        
        response.raise_for_status()
        return response.content
    except httpx.HTTPStatusError as e:
        logger.error(f"Text2Image service returned error: {e.response.text}")
        raise HTTPException(status_code=e.response.status_code, detail=f"Text2Image service error: {e.response.text}")
    except httpx.RequestError as e:
        logger.error(f"Error connecting to Text2Image service: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Text2Image service unavailable: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in Text2Image processing: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Text2Image processing failed: {str(e)}")

@app.post("/tryon")
async def tryon_page(
    request: Request,
    model_image: UploadFile = File(...),
    garment_image: UploadFile = File(...),
    category: str = Form("auto"),
    mode: str = Form("quality")
):
    """Handle virtual try-on request from the web UI"""
    start_time = time.time()
    request_id = str(uuid.uuid4())
    
    try:
        # Read uploaded files
        model_image_contents = await model_image.read()
        garment_image_contents = await garment_image.read()
        
        # Save model image
        model_image_path = await save_uploaded_image(model_image_contents, model_image.filename)
        model_image_rel_path = os.path.relpath(model_image_path, UPLOAD_FOLDER)
        model_image_url = f"/static/uploads/{model_image_rel_path}"
        
        # Save garment image
        garment_image_path = await save_uploaded_image(garment_image_contents, garment_image.filename)
        garment_image_rel_path = os.path.relpath(garment_image_path, UPLOAD_FOLDER)
        garment_image_url = f"/static/uploads/{garment_image_rel_path}"
        
        # Convert images to base64
        model_image_b64 = base64.b64encode(model_image_contents).decode('utf-8')
        garment_image_b64 = base64.b64encode(garment_image_contents).decode('utf-8')
        
        # Validate mode
        valid_modes = ["quality", "balanced", "performance"]
        if mode not in valid_modes:
            logger.warning(f"Invalid mode '{mode}', defaulting to 'quality'")
            mode = "quality"
        
        # Process virtual try-on request
        async with httpx.AsyncClient() as client:
            tryon_result = await process_virtual_tryon(
                client, 
                model_image_b64,
                garment_image_b64,
                category=category,
                mode=mode
            )
        
        # Get result image path and data
        result_image_path = tryon_result["result_image_path"]
        result_image_data = tryon_result["result_image_data"]
        
        # Save result image
        result_filename = os.path.basename(result_image_path)
        result_path = os.path.join(RESULTS_FOLDER, result_filename)
        
        async with aiofiles.open(result_path, 'wb') as f:
            await f.write(base64.b64decode(result_image_data))
        
        result_url = f"/static/results/{result_filename}"
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Generate HTML response
        html_response = generate_tryon_result_html(
            request_id=request_id,
            model_img=model_image_url,
            garment_img=garment_image_url,
            result_img=result_url,
            category=category,
            mode=mode,
            processing_time=processing_time,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        return HTMLResponse(content=html_response)
    
    except Exception as e:
        logger.error(f"Error processing virtual try-on: {str(e)}")
        return HTMLResponse(
            content=f"""
            <html>
                <head>
                    <title>Error</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; margin: 40px; }}
                        .error {{ color: red; background: #ffeeee; padding: 20px; border-radius: 5px; }}
                        a {{ display: inline-block; margin-top: 20px; }}
                    </style>
                </head>
                <body>
                    <h1>Virtual Try-On Error</h1>
                    <div class="error">
                        <p>Failed to process your request:</p>
                        <p>{str(e)}</p>
                    </div>
                    <a href="/">Back to Home</a>
                </body>
            </html>
            """,
            status_code=500
        )

@app.post("/api/tryon")
async def api_tryon(
    model_image: UploadFile = File(...),
    garment_image: UploadFile = File(...),
    category: str = Form("auto"),
    mode: str = Form("quality")
):
    """API endpoint for virtual try-on"""
    try:
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Read uploaded files
        model_image_contents = await model_image.read()
        garment_image_contents = await garment_image.read()
        
        # Save model image
        model_image_path = await save_uploaded_image(model_image_contents, model_image.filename)
        model_image_rel_path = os.path.relpath(model_image_path, UPLOAD_FOLDER)
        model_image_url = f"/static/uploads/{model_image_rel_path}"
        
        # Save garment image
        garment_image_path = await save_uploaded_image(garment_image_contents, garment_image.filename)
        garment_image_rel_path = os.path.relpath(garment_image_path, UPLOAD_FOLDER)
        garment_image_url = f"/static/uploads/{garment_image_rel_path}"
        
        # Convert images to base64
        model_image_b64 = base64.b64encode(model_image_contents).decode('utf-8')
        garment_image_b64 = base64.b64encode(garment_image_contents).decode('utf-8')
        
        # Process virtual try-on request
        async with httpx.AsyncClient() as client:
            tryon_result = await process_virtual_tryon(
                client, 
                model_image_b64,
                garment_image_b64,
                category=category,
                mode=mode
            )
        
        # Get result image path and data
        result_image_path = tryon_result["result_image_path"]
        result_image_data = tryon_result["result_image_data"]
        
        # Save result image
        result_filename = os.path.basename(result_image_path)
        result_path = os.path.join(RESULTS_FOLDER, result_filename)
        
        async with aiofiles.open(result_path, 'wb') as f:
            await f.write(base64.b64decode(result_image_data))
        
        result_url = f"/static/results/{result_filename}"
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Return response
        return {
            "request_id": request_id,
            "model_image": model_image_url,
            "garment_image": garment_image_url,
            "result_image": result_url,
            "category": category,
            "processing_time": processing_time,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "details": tryon_result["details"] if "details" in tryon_result else {}
        }
    
    except Exception as e:
        logger.error(f"API virtual try-on error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Virtual try-on processing failed: {str(e)}")

def generate_tryon_result_html(request_id, model_img, garment_img, result_img, category, mode, processing_time, timestamp):
    """Generate HTML for displaying virtual try-on results"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Virtual Try-On Results</title>
        <style>
            body {{ 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                max-width: 900px; 
                margin: 0 auto; 
                padding: 20px;
                background-color: #f9f9f9;
                color: #333;
            }}
            h1 {{ 
                color: #2c3e50; 
                text-align: center;
                margin-bottom: 30px;
            }}
            .result-container {{ 
                background-color: white;
                padding: 25px;
                border-radius: 8px;
                box-shadow: 0 3px 10px rgba(0,0,0,0.1);
                margin-bottom: 30px;
            }}
            .image-grid {{
                display: flex;
                flex-wrap: wrap;
                gap: 20px;
                margin: 20px 0;
            }}
            .image-card {{
                flex: 1;
                min-width: 250px;
                background: white;
                border-radius: 8px;
                padding: 15px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }}
            .image-card img {{
                width: 100%;
                height: auto;
                border-radius: 5px;
                max-height: 400px;
                object-fit: contain;
            }}
            .image-card h3 {{
                margin-top: 10px;
                margin-bottom: 10px;
                color: #3498db;
            }}
            .meta-info {{
                background-color: #f1f1f1;
                padding: 15px;
                border-radius: 5px;
                margin-top: 20px;
                font-size: 0.9em;
                color: #666;
            }}
            .back-button {{
                display: inline-block;
                margin-top: 20px;
                padding: 12px 20px;
                background-color: #3498db;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                font-weight: 500;
                transition: all 0.3s ease;
                text-align: center;
            }}
            .back-button:hover {{
                background-color: #2980b9;
                box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            }}
            .result-title {{
                color: #3498db;
                margin-bottom: 20px;
                text-align: center;
            }}
            .meta-info p {{
                margin: 8px 0;
            }}
        </style>
    </head>
    <body>
        <h1>Virtual Try-On Results</h1>
        
        <div class="result-container">
            <h2 class="result-title">Your Virtual Outfit</h2>
            
            <div class="image-grid">
                <div class="image-card">
                    <h3>Model Image</h3>
                    <img src="{model_img}" alt="Model Image">
                </div>
                
                <div class="image-card">
                    <h3>Garment Image</h3>
                    <img src="{garment_img}" alt="Garment Image">
                </div>
                
                <div class="image-card">
                    <h3>Result</h3>
                    <img src="{result_img}" alt="Try-On Result">
                </div>
            </div>
            
            <div class="meta-info">
                <p><strong>Request ID:</strong> {request_id}</p>
                <p><strong>Category:</strong> {category}</p>
                <p><strong>Processing Mode:</strong> {mode}</p>
                <p><strong>Processing Time:</strong> {processing_time:.2f} seconds</p>
                <p><strong>Timestamp:</strong> {timestamp}</p>
            </div>
        </div>
        
        <a href="/" class="back-button">Back to Home</a>
    </body>
    </html>
    """

async def process_multi_garment_tryon(
    client: httpx.AsyncClient,
    model_image_b64: str,
    top_image_b64: Optional[str],
    bottom_image_b64: Optional[str],
    mode: str = "quality"
) -> Dict:
    """Process multi-garment virtual try-on request through the Virtual Try-On IEP"""
    try:
        payload = {
            "model_image_data": model_image_b64,
            "top_image_data": top_image_b64,
            "bottom_image_data": bottom_image_b64,
            "mode": mode
        }
        
        response = await client.post(
            f"{VIRTUAL_TRYON_SERVICE_URL}/multi-tryon",
            json=payload,
            timeout=float(SERVICE_TIMEOUT)
        )
        
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"Multi-Garment Try-On service returned error: {e.response.text}")
        raise HTTPException(status_code=e.response.status_code, detail=f"Multi-Garment Try-On service error: {e.response.text}")
    except httpx.RequestError as e:
        logger.error(f"Error connecting to Multi-Garment Try-On service: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Multi-Garment Try-On service unavailable: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in Multi-Garment Try-On processing: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Multi-Garment Try-On processing failed: {str(e)}")

@app.post("/tryon/multi")
async def multi_tryon_page(
    request: Request,
    model_image: UploadFile = File(...),
    top_image: Optional[UploadFile] = None,
    bottom_image: Optional[UploadFile] = None,
    mode: str = Form("quality")
):
    """Handle multi-garment virtual try-on request from the web UI"""
    start_time = time.time()
    request_id = str(uuid.uuid4())
    
    # Validate that at least one garment is provided
    if top_image is None and bottom_image is None:
        return HTMLResponse(
            content="""
            <html>
                <head>
                    <title>Error</title>
                    <style>
                        body { font-family: Arial, sans-serif; margin: 40px; }
                        .error { color: red; background: #ffeeee; padding: 20px; border-radius: 5px; }
                        a { display: inline-block; margin-top: 20px; color: #3498db; }
                    </style>
                </head>
                <body>
                    <h1>Multi-Garment Try-On Error</h1>
                    <div class="error">
                        <p>At least one garment (top or bottom) must be provided.</p>
                    </div>
                    <a href="/">Back to Home</a>
                </body>
            </html>
            """,
            status_code=400
        )
    
    try:
        # Read uploaded model image
        model_image_contents = await model_image.read()
        
        # Save model image
        model_image_path = await save_uploaded_image(model_image_contents, model_image.filename)
        model_image_rel_path = os.path.relpath(model_image_path, UPLOAD_FOLDER)
        model_image_url = f"/static/uploads/{model_image_rel_path}"
        
        # Convert model image to base64
        model_image_b64 = base64.b64encode(model_image_contents).decode('utf-8')
        
        # Process top image if provided
        top_image_b64 = None
        top_image_url = None
        if top_image:
            top_image_contents = await top_image.read()
            top_image_path = await save_uploaded_image(top_image_contents, top_image.filename)
            top_image_rel_path = os.path.relpath(top_image_path, UPLOAD_FOLDER)
            top_image_url = f"/static/uploads/{top_image_rel_path}"
            top_image_b64 = base64.b64encode(top_image_contents).decode('utf-8')
        
        # Process bottom image if provided
        bottom_image_b64 = None
        bottom_image_url = None
        if bottom_image:
            bottom_image_contents = await bottom_image.read()
            bottom_image_path = await save_uploaded_image(bottom_image_contents, bottom_image.filename)
            bottom_image_rel_path = os.path.relpath(bottom_image_path, UPLOAD_FOLDER)
            bottom_image_url = f"/static/uploads/{bottom_image_rel_path}"
            bottom_image_b64 = base64.b64encode(bottom_image_contents).decode('utf-8')
        
        # Validate mode
        valid_modes = ["quality", "balanced", "performance"]
        if mode not in valid_modes:
            logger.warning(f"Invalid mode '{mode}', defaulting to 'quality'")
            mode = "quality"
        
        # Process multi-garment try-on request
        async with httpx.AsyncClient() as client:
            tryon_result = await process_multi_garment_tryon(
                client, 
                model_image_b64,
                top_image_b64,
                bottom_image_b64,
                mode=mode
            )
        
        # Get final result image path and data
        final_result_path = tryon_result["final_result_path"]
        final_result_data = tryon_result["final_result_data"]
        
        # Save result image
        result_filename = os.path.basename(final_result_path)
        result_path = os.path.join(RESULTS_FOLDER, result_filename)
        
        async with aiofiles.open(result_path, 'wb') as f:
            await f.write(base64.b64decode(final_result_data))
        
        result_url = f"/static/results/{result_filename}"
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Generate HTML response
        html_response = generate_multi_tryon_result_html(
            request_id=request_id,
            model_img=model_image_url,
            top_img=top_image_url,
            bottom_img=bottom_image_url,
            result_img=result_url,
            mode=mode,
            processing_time=processing_time,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        return HTMLResponse(content=html_response)
    
    except Exception as e:
        logger.error(f"Error processing multi-garment try-on: {str(e)}")
        logger.error(traceback.format_exc())
        return HTMLResponse(
            content=f"""
            <html>
                <head>
                    <title>Error</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; margin: 40px; }}
                        .error {{ color: red; background: #ffeeee; padding: 20px; border-radius: 5px; }}
                        a {{ display: inline-block; margin-top: 20px; }}
                    </style>
                </head>
                <body>
                    <h1>Multi-Garment Try-On Error</h1>
                    <div class="error">
                        <p>Failed to process your request:</p>
                        <p>{str(e)}</p>
                    </div>
                    <a href="/">Back to Home</a>
                </body>
            </html>
            """,
            status_code=500
        )

def generate_multi_tryon_result_html(request_id, model_img, top_img, bottom_img, result_img, mode, processing_time, timestamp):
    """Generate HTML for displaying multi-garment try-on results"""
    
    garments_html = ""
    if top_img:
        garments_html += f'''
        <div class="image-card">
            <h3>Top Garment</h3>
            <img src="{top_img}" alt="Top Garment Image">
        </div>
        '''
    
    if bottom_img:
        garments_html += f'''
        <div class="image-card">
            <h3>Bottom Garment</h3>
            <img src="{bottom_img}" alt="Bottom Garment Image">
        </div>
        '''
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Multi-Garment Try-On Results</title>
        <style>
            body {{ 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                max-width: 900px; 
                margin: 0 auto; 
                padding: 20px;
                background-color: #f9f9f9;
                color: #333;
            }}
            h1 {{ 
                color: #2c3e50; 
                text-align: center;
                margin-bottom: 30px;
            }}
            .result-container {{ 
                background-color: white;
                padding: 25px;
                border-radius: 8px;
                box-shadow: 0 3px 10px rgba(0,0,0,0.1);
                margin-bottom: 30px;
            }}
            .image-grid {{
                display: flex;
                flex-wrap: wrap;
                gap: 20px;
                margin: 20px 0;
            }}
            .image-card {{
                flex: 1;
                min-width: 250px;
                background: white;
                border-radius: 8px;
                padding: 15px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }}
            .image-card img {{
                width: 100%;
                height: auto;
                border-radius: 5px;
                max-height: 400px;
                object-fit: contain;
            }}
            .image-card h3 {{
                margin-top: 10px;
                margin-bottom: 10px;
                color: #3498db;
            }}
            .meta-info {{
                background-color: #f1f1f1;
                padding: 15px;
                border-radius: 5px;
                margin-top: 20px;
                font-size: 0.9em;
                color: #666;
            }}
            .back-button {{
                display: inline-block;
                margin-top: 20px;
                padding: 12px 20px;
                background-color: #3498db;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                font-weight: 500;
                transition: all 0.3s ease;
                text-align: center;
            }}
            .back-button:hover {{
                background-color: #2980b9;
                box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            }}
            .result-title {{
                color: #3498db;
                margin-bottom: 20px;
                text-align: center;
            }}
            .meta-info p {{
                margin: 8px 0;
            }}
        </style>
    </head>
    <body>
        <h1>Multi-Garment Virtual Try-On Results</h1>
        
        <div class="result-container">
            <h2 class="result-title">Your Virtual Outfit</h2>
            
            <div class="image-grid">
                <div class="image-card">
                    <h3>Model Image</h3>
                    <img src="{model_img}" alt="Model Image">
                </div>
                
                {garments_html}
                
                <div class="image-card">
                    <h3>Final Result</h3>
                    <img src="{result_img}" alt="Try-On Result">
                </div>
            </div>
            
            <div class="meta-info">
                <p><strong>Request ID:</strong> {request_id}</p>
                <p><strong>Processing Mode:</strong> {mode}</p>
                <p><strong>Processing Time:</strong> {processing_time:.2f} seconds</p>
                <p><strong>Timestamp:</strong> {timestamp}</p>
            </div>
        </div>
        
        <a href="/" class="back-button">Back to Home</a>
    </body>
    </html>
    """

@app.post("/api/elegance/chat")
async def api_elegance_chat(request: Request):
    """Proxy endpoint for the Elegance chatbot API"""
    try:
        # Get raw request body
        data = await request.json()
        message = data.get("message", "")
        session_id = data.get("session_id", "")
        
        logger.info(f"Received chat message for Elegance: {message[:30]}...")
        
        # Create a proper payload for the Elegance chatbot API
        payload = {
            "messages": [{"role": "user", "content": message}],
            "session_id": session_id
        }
        
        # Forward the request to the Elegance chatbot
        async with httpx.AsyncClient(timeout=SERVICE_TIMEOUT) as client:
            # Use internal Docker network communication
            elegance_url = f"{ELEGANCE_SERVICE_URL}/api/chat"
            
            logger.info(f"Sending request to Elegance API at: {elegance_url}")
            
            response = await client.post(
                elegance_url,
                json=payload,
                timeout=SERVICE_TIMEOUT
            )
            
            if response.status_code != 200:
                logger.error(f"Error from Elegance API: {response.text}")
                return JSONResponse(
                    status_code=response.status_code,
                    content={"error": response.text, "response": "Sorry, there was an error processing your request."}
                )
            
            resp_data = response.json()
            logger.info(f"Received response from Elegance: {resp_data.get('response', '')[:30]}...")
            return resp_data
    except Exception as e:
        logger.error(f"Error in elegance chat: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "response": "Je suis désolé! There was an error communicating with Elegance. Please try again."}
        )

@app.post("/recommendation")
async def get_recommendation(
    request: Request,
    request_id: str = Form(...),
    detection_id: str = Form(...),
    operation: str = Form(...),  # "matching" or "similarity"
    item_type: str = Form(...),  # "topwear" or "bottomwear"
    gender: Optional[str] = Form(None),
    style: Optional[str] = Form(None)
):
    """Endpoint to get recommendations for a detected item"""
    try:
        # Get analysis results from global store
        analysis_results = analysis_results_store.get(request_id)
        
        if not analysis_results:
            logger.error(f"Analysis results not found for request_id: {request_id}")
            raise HTTPException(status_code=404, detail="Analysis results not found")
        
        # Get the specific detection
        detection_index = int(detection_id)
        if detection_index >= len(analysis_results.get("detections", [])):
            logger.error(f"Detection index {detection_index} out of range")
            raise HTTPException(status_code=404, detail="Detection not found")
            
        detection = analysis_results["detections"][detection_index]
        
        # Get the appropriate vector based on operation
        vector = None
        if operation == "matching":
            vector = detection.get("color_histogram")
        else:  # similarity
            vector = detection.get("features")
            
        if not vector:
            logger.error(f"No {'color' if operation == 'matching' else 'feature'} vector available")
            raise HTTPException(status_code=400, 
                              detail=f"No {'color' if operation == 'matching' else 'feature'} vector available")
        
        # Create client for recommendation request
        async with httpx.AsyncClient() as client:
            # Process the recommendation
            result_image = await process_recommendation(
                client=client,
                vector=vector,
                gender=gender,
                style=style,
                item_type=item_type,
                operation=operation
            )
            
            # Return the image directly
            return StreamingResponse(io.BytesIO(result_image), media_type="image/jpeg")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in recommendation: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error processing recommendation: {str(e)}")

@app.post("/api/recommendation")
async def api_get_recommendation(request: Request, recommendation: RecommendationRequest):
    """API endpoint to get recommendations for a detected item using JSON request body"""
    try:
        # Get analysis results from global store
        analysis_results = analysis_results_store.get(recommendation.request_id)
        
        if not analysis_results:
            logger.error(f"Analysis results not found for request_id: {recommendation.request_id}")
            return JSONResponse(
                status_code=404,
                content={"error": "Analysis results not found", "detail": f"No results found for request ID {recommendation.request_id}"}
            )
        
        # Get the specific detection
        detection_index = int(recommendation.detection_id)
        if detection_index >= len(analysis_results.get("detections", [])):
            logger.error(f"Detection index {detection_index} out of range")
            return JSONResponse(
                status_code=404,
                content={"error": "Detection not found", "detail": f"Detection index {detection_index} is out of range"}
            )
            
        detection = analysis_results["detections"][detection_index]
        
        # Get the appropriate vector based on operation
        vector = None
        if recommendation.operation == "matching":
            vector = detection.get("color_histogram")
        else:  # similarity
            vector = detection.get("features")
            
        if not vector:
            logger.error(f"No {'color' if recommendation.operation == 'matching' else 'feature'} vector available")
            return JSONResponse(
                status_code=400,
                content={"error": "Vector not available", 
                       "detail": f"No {'color' if recommendation.operation == 'matching' else 'feature'} vector available for this item"}
            )
        
        # Create client for recommendation request
        async with httpx.AsyncClient() as client:
            # Process the recommendation
            result_image = await process_recommendation(
                client=client,
                vector=vector,
                gender=recommendation.gender,
                style=recommendation.style,
                item_type=recommendation.item_type,
                operation=recommendation.operation
            )
            
            # Return the image directly as a base64 string
            base64_image = base64.b64encode(result_image).decode('utf-8')
            return JSONResponse(
                content={
                    "image_data": base64_image,
                    "content_type": "image/jpeg"
                }
            )
            
    except Exception as e:
        logger.error(f"Error in API recommendation: {traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={"error": "Recommendation error", "detail": str(e)}
        )

# Additional models for match response
class MatchAnalysisItem(BaseModel):
    score: int
    analysis: str

class MatchAnalysis(BaseModel):
    color_harmony: MatchAnalysisItem
    style_consistency: MatchAnalysisItem
    occasion_appropriateness: MatchAnalysisItem
    trend_alignment: Optional[MatchAnalysisItem] = None
    feature_match: Optional[MatchAnalysisItem] = None
    color_histogram_match: Optional[MatchAnalysisItem] = None
    
    # Allow additional fields beyond the ones explicitly defined
    class Config:
        extra = "allow"

class MatchResponse(BaseModel):
    match_score: int
    analysis: Dict[str, Dict[str, Union[int, str]]]  # More flexible structure
    suggestions: List[str]
    alternative_pairings: Optional[List[Dict[str, Any]]] = None
    
    # Allow additional fields beyond the ones explicitly defined
    class Config:
        extra = "allow"

# Function to process match request
async def process_match(
    client: httpx.AsyncClient,
    topwear_data: bytes,
    bottomwear_data: bytes
) -> Dict:
    """
    Process match request by:
    1. Sending images to detection-iep to identify clothing items
    2. Sending images to style-iep for style classification
    3. Extracting specific garments and sending to feature-iep
    4. Preparing payload with all extracted data
    5. Sending preprocessed data to match-iep for final scoring
    
    Args:
        client: httpx client
        topwear_data: image data for top clothing item
        bottomwear_data: image data for bottom clothing item
        
    Returns:
        dict: match results
    """
    try:
        logger.info("Processing match request through centralized pipeline")
        
        # STEP 1: Send both images to detection-iep
        logger.info("Sending images to Detection IEP")
        detection_tasks = [
            client.post(
                f"{DETECTION_SERVICE_URL}/detect",
                files={"file": ("topwear.jpg", topwear_data, "image/jpeg")},
                timeout=SERVICE_TIMEOUT
            ),
            client.post(
                f"{DETECTION_SERVICE_URL}/detect",
                files={"file": ("bottomwear.jpg", bottomwear_data, "image/jpeg")},
                timeout=SERVICE_TIMEOUT
            )
        ]
        top_detection_response, bottom_detection_response = await asyncio.gather(*detection_tasks)
        
        if top_detection_response.status_code != 200 or bottom_detection_response.status_code != 200:
            logger.error(f"Detection IEP error: Top status={top_detection_response.status_code}, Bottom status={bottom_detection_response.status_code}")
            return {"error": "Detection service error"}
        
        top_detection_result = top_detection_response.json()
        bottom_detection_result = bottom_detection_response.json()
        
        # STEP 2: Send both images to style-iep
        logger.info("Sending images to Style IEP")
        style_tasks = [
            client.post(
                f"{STYLE_SERVICE_URL}/classify",
                files={"file": ("topwear.jpg", topwear_data, "image/jpeg")},
                timeout=SERVICE_TIMEOUT
            ),
            client.post(
                f"{STYLE_SERVICE_URL}/classify",
                files={"file": ("bottomwear.jpg", bottomwear_data, "image/jpeg")},
                timeout=SERVICE_TIMEOUT
            )
        ]
        top_style_response, bottom_style_response = await asyncio.gather(*style_tasks)
        
        if top_style_response.status_code != 200 or bottom_style_response.status_code != 200:
            logger.error(f"Style IEP error: Top status={top_style_response.status_code}, Bottom status={bottom_style_response.status_code}")
            return {"error": "Style service error"}
        
        top_style_result = top_style_response.json()
        bottom_style_result = bottom_style_response.json()
        
        # STEP 3: Extract specific garments from detection results
        # Find shirt in topwear
        top_shirt = None
        top_shirt_crop = None
        
        if "detections" in top_detection_result:
            for detection in top_detection_result["detections"]:
                if detection.get("class_name") in ["Shirt", "T-Shirt", "Shirt/T-Shirt", "Top"]:
                    top_shirt = detection
                    # Extract crop from the image using bbox
                    try:
                        import io
                        from PIL import Image
                        # Convert to PIL image
                        top_image = Image.open(io.BytesIO(topwear_data)).convert('RGB')
                        # Extract crop
                        bbox = detection.get("bbox", [0, 0, 0, 0])
                        if len(bbox) == 4:
                            x_min, y_min, x_max, y_max = bbox
                            # Ensure bbox is within image bounds
                            width, height = top_image.size
                            x_min = max(0, x_min)
                            y_min = max(0, y_min)
                            x_max = min(width, x_max)
                            y_max = min(height, y_max)
                            
                            if x_max > x_min and y_max > y_min:
                                top_shirt_crop = top_image.crop((x_min, y_min, x_max, y_max))
                    except Exception as e:
                        logger.error(f"Error extracting top shirt crop: {str(e)}")
                    break
        
        # Find pants in bottomwear
        bottom_pants = None
        bottom_pants_crop = None
        
        if "detections" in bottom_detection_result:
            for detection in bottom_detection_result["detections"]:
                if detection.get("class_name") in ["Pants", "Shorts", "Pants/Shorts"]:
                    bottom_pants = detection
                    # Extract crop from the image using bbox
                    try:
                        import io
                        from PIL import Image
                        # Convert to PIL image
                        bottom_image = Image.open(io.BytesIO(bottomwear_data)).convert('RGB')
                        # Extract crop
                        bbox = detection.get("bbox", [0, 0, 0, 0])
                        if len(bbox) == 4:
                            x_min, y_min, x_max, y_max = bbox
                            # Ensure bbox is within image bounds
                            width, height = bottom_image.size
                            x_min = max(0, x_min)
                            y_min = max(0, y_min)
                            x_max = min(width, x_max)
                            y_max = min(height, y_max)
                            
                            if x_max > x_min and y_max > y_min:
                                bottom_pants_crop = bottom_image.crop((x_min, y_min, x_max, y_max))
                    except Exception as e:
                        logger.error(f"Error extracting bottom pants crop: {str(e)}")
                    break
        
        # STEP 4: Extract features for the specific garments or full images
        logger.info("Extracting features")
        
        # Prepare images for feature extraction
        top_feature_image = topwear_data
        bottom_feature_image = bottomwear_data
        
        # If we have crops, use them instead
        if top_shirt_crop:
            import io
            top_crop_bytes = io.BytesIO()
            top_shirt_crop.save(top_crop_bytes, format='JPEG')
            top_feature_image = top_crop_bytes.getvalue()
        
        if bottom_pants_crop:
            import io
            bottom_crop_bytes = io.BytesIO()
            bottom_pants_crop.save(bottom_crop_bytes, format='JPEG')
            bottom_feature_image = bottom_crop_bytes.getvalue()
        
        # Send feature extraction requests
        feature_tasks = [
            client.post(
                f"{FEATURE_SERVICE_URL}/extract",
                files={"file": ("top_feature.jpg", top_feature_image, "image/jpeg")},
                timeout=SERVICE_TIMEOUT
            ),
            client.post(
                f"{FEATURE_SERVICE_URL}/extract",
                files={"file": ("bottom_feature.jpg", bottom_feature_image, "image/jpeg")},
                timeout=SERVICE_TIMEOUT
            )
        ]
        top_feature_response, bottom_feature_response = await asyncio.gather(*feature_tasks)
        
        if top_feature_response.status_code != 200 or bottom_feature_response.status_code != 200:
            logger.error(f"Feature IEP error: Top status={top_feature_response.status_code}, Bottom status={bottom_feature_response.status_code}")
            # We'll continue even if feature extraction fails, as match-iep can handle missing features
        
        top_feature_result = top_feature_response.json() if top_feature_response.status_code == 200 else {"error": "Feature extraction failed"}
        bottom_feature_result = bottom_feature_response.json() if bottom_feature_response.status_code == 200 else {"error": "Feature extraction failed"}
        
        # STEP 5: Prepare payload for match-iep with all preprocessed data
        # Extract top style
        top_style = "unknown"
        if "styles" in top_style_result and top_style_result["styles"]:
            # Sort by confidence and take the highest
            sorted_styles = sorted(top_style_result["styles"], key=lambda x: x["confidence"], reverse=True)
            top_style = sorted_styles[0]["style_name"].lower()
        
        # Extract bottom style
        bottom_style = "unknown"
        if "styles" in bottom_style_result and bottom_style_result["styles"]:
            # Sort by confidence and take the highest
            sorted_styles = sorted(bottom_style_result["styles"], key=lambda x: x["confidence"], reverse=True)
            bottom_style = sorted_styles[0]["style_name"].lower()
        
        # Get feature vectors
        top_vector = top_feature_result.get("features", None)
        bottom_vector = bottom_feature_result.get("features", None)
        
        # Get color histograms
        top_histogram = top_feature_result.get("color_histogram", None)
        bottom_histogram = bottom_feature_result.get("color_histogram", None)
        
        # Build match request
        match_request = {
            "top_style": top_style,
            "bottom_style": bottom_style,
            "top_vector": top_vector,
            "bottom_vector": bottom_vector,
            "top_histogram": top_histogram,
            "bottom_histogram": bottom_histogram,
            "top_detection": top_shirt or {},
            "bottom_detection": bottom_pants or {}
        }
        
        # STEP 6: Send preprocessed data to Match IEP
        logger.info("Sending preprocessed data to Match IEP")
        match_response = await client.post(
            f"{MATCH_SERVICE_URL}/compute_match",
            json=match_request,
            timeout=SERVICE_TIMEOUT
        )
        
        if match_response.status_code != 200:
            logger.error(f"Match IEP error: {match_response.status_code} - {match_response.text}")
            return {"error": "Match service error"}
        
        # Get the match result
        match_result = match_response.json()
        
        # Validate the match result structure
        logger.info(f"Match result received with keys: {list(match_result.keys())}")
        
        # Check if expected fields are present
        required_fields = ["match_score", "analysis", "suggestions"]
        missing_fields = [field for field in required_fields if field not in match_result]
        
        if missing_fields:
            logger.error(f"Match result missing required fields: {missing_fields}")
            # Add default values for missing fields to prevent frontend errors
            for field in missing_fields:
                if field == "match_score":
                    match_result["match_score"] = 50  # Default score
                elif field == "analysis":
                    match_result["analysis"] = {
                        "default": {
                            "score": 50,
                            "analysis": "Analysis data unavailable"
                        }
                    }
                elif field == "suggestions":
                    match_result["suggestions"] = ["No specific suggestions available"]
        
        # Return the validated match result
        return match_result
        
    except Exception as e:
        logger.error(f"Error in match processing: {str(e)}")
        logger.error(traceback.format_exc())  # Add stack trace for better debugging
        return {"error": f"Match processing error: {str(e)}"}

@app.post("/match")
async def match_outfit(
    request: Request,
    topwear: UploadFile = File(...),
    bottomwear: UploadFile = File(...)
):
    """
    Match a topwear item with a bottomwear item and evaluate compatibility
    """
    try:
        # Record start time
        start_time = time.time()
        
        # Generate request ID
        request_id = str(uuid.uuid4())
        
        # Get file contents
        topwear_content = await topwear.read()
        bottomwear_content = await bottomwear.read()
        
        # Save uploaded images
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        topwear_filename = f"{timestamp}_topwear_{request_id}.jpg"
        bottomwear_filename = f"{timestamp}_bottomwear_{request_id}.jpg"
        
        topwear_path = await save_uploaded_image(topwear_content, topwear_filename)
        bottomwear_path = await save_uploaded_image(bottomwear_content, bottomwear_filename)
        
        # Get public URLs
        topwear_url = f"/static/uploads/{topwear_filename}"
        bottomwear_url = f"/static/uploads/{bottomwear_filename}"
        
        # Process match
        async with httpx.AsyncClient() as client:
            match_result = await process_match(client, topwear_content, bottomwear_content)
        
        # Check for errors
        if "error" in match_result:
            raise HTTPException(status_code=500, detail=match_result["error"])
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Log result
        logger.info(f"Match processed successfully in {processing_time:.2f}s with score {match_result['match_score']}")
        
        # Generate HTML for the results page
        html_result = generate_match_result_html(
            topwear_img=topwear_url,
            bottomwear_img=bottomwear_url,
            match_result=match_result,
            processing_time=processing_time,
            timestamp=datetime.now().isoformat()
        )
        
        return HTMLResponse(content=html_result, status_code=200)
        
    except Exception as e:
        logger.error(f"Error processing match request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Match analysis failed: {str(e)}")

# Add API endpoint for match (JSON request/response)
@app.post("/api/match", response_model=MatchResponse)
async def api_match_outfit(
    topwear: UploadFile = File(...),
    bottomwear: UploadFile = File(...)
):
    """
    API endpoint for matching a topwear item with a bottomwear item
    """
    try:
        # Get file contents
        topwear_content = await topwear.read()
        bottomwear_content = await bottomwear.read()
        
        # Process match
        async with httpx.AsyncClient() as client:
            logger.info(f"API match request: Sending to process_match")
            match_result = await process_match(client, topwear_content, bottomwear_content)
        
        # Check for errors
        if "error" in match_result:
            logger.error(f"Error in match result: {match_result['error']}")
            raise HTTPException(status_code=500, detail=match_result["error"])
        
        # Log the structure of the match_result for debugging
        logger.info(f"Match result keys: {list(match_result.keys())}")
        if "match_score" in match_result:
            logger.info(f"Match score: {match_result['match_score']}")
        else:
            logger.error("No match_score in result")
            
        if "analysis" in match_result:
            logger.info(f"Analysis keys: {list(match_result['analysis'].keys())}")
        else:
            logger.error("No analysis in result")
            
        if "suggestions" in match_result:
            logger.info(f"Number of suggestions: {len(match_result['suggestions'])}")
        else:
            logger.error("No suggestions in result")
        
        # Log the complete response JSON for debugging (truncate if too large)
        import json
        response_json = json.dumps(match_result)
        if len(response_json) > 1000:
            logger.info(f"API match response (truncated): {response_json[:1000]}...")
        else:
            logger.info(f"API match response: {response_json}")
            
        # Validate that the response can be properly serialized as the MatchResponse model
        try:
            # This will fail if the structure doesn't match the model definition
            response_obj = MatchResponse(
                match_score=match_result["match_score"],
                analysis=match_result["analysis"],
                suggestions=match_result.get("suggestions", []),
                alternative_pairings=match_result.get("alternative_pairings", [])
            )
            logger.info("Response successfully validated against MatchResponse model")
        except Exception as e:
            logger.error(f"Response validation failed: {str(e)}")
            # Fix any issues with the response structure
            if not isinstance(match_result["match_score"], int):
                match_result["match_score"] = int(float(match_result["match_score"]))
                
            # Ensure analysis is properly structured
            if not isinstance(match_result["analysis"], dict):
                logger.error(f"Analysis is not a dict: {type(match_result['analysis'])}")
                match_result["analysis"] = {
                    "default": {
                        "score": 50,
                        "analysis": "Analysis data unavailable"
                    }
                }
            
            # Ensure suggestions is a list of strings
            if "suggestions" not in match_result or not isinstance(match_result["suggestions"], list):
                match_result["suggestions"] = ["No specific suggestions available"]
        
        # Return the match result
        logger.info("Returning API match result to frontend")
        return match_result
        
    except Exception as e:
        logger.error(f"Error processing API match request: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Match analysis failed: {str(e)}")

def generate_match_result_html(topwear_img, bottomwear_img, match_result, processing_time, timestamp):
    """Generate HTML for displaying match analysis results"""
    
    # Extract match scores and analysis
    match_score = match_result["match_score"]
    analysis = match_result["analysis"]
    suggestions = match_result["suggestions"]
    
    # Generate analysis HTML
    analysis_items_html = ""
    for key, item in analysis.items():
        # Format the category name nicely
        if key == "color_harmony":
            category_name = "Dominant Colors (K-means)"
        elif key == "color_histogram_match":
            category_name = "Color Distribution Analysis"
        else:
            category_name = key.replace('_', ' ').title()
        
        # Calculate percentage width for the score bar
        score = item["score"]
        score_percentage = score
        
        # Determine color based on score
        if score >= 80:
            color_class = "excellent"
        elif score >= 65:
            color_class = "good"
        elif score >= 50:
            color_class = "average"
        else:
            color_class = "poor"
            
        analysis_items_html += f"""
        <div class="analysis-item">
            <div class="analysis-header">
                <h3>{category_name}</h3>
                <div class="score-indicator {color_class}">{score}/100</div>
            </div>
            <div class="score-bar-container">
                <div class="score-bar {color_class}" style="width: {score_percentage}%;"></div>
            </div>
            <p class="analysis-text">{item["analysis"]}</p>
        </div>
        """
    
    # Generate suggestions HTML
    suggestions_html = ""
    if suggestions:
        suggestions_html = "<h3>Style Suggestions</h3><ul class='suggestions-list'>"
        for suggestion in suggestions:
            suggestions_html += f"<li><i class='suggestion-icon'>💡</i> {suggestion}</li>"
        suggestions_html += "</ul>"
    
    # Add a section explaining the different color analysis methods
    color_analysis_explanation = """
    <div class="analysis-explanation">
        <h3>About Color Analysis</h3>
        <p><strong>Dominant Colors (K-means):</strong> Analyzes the primary colors extracted using K-means clustering and evaluates their harmony based on color theory principles.</p>
        <p><strong>Color Distribution Analysis:</strong> Evaluates the detailed color histogram pattern using both similarity and entropy measures to assess overall color compatibility.</p>
    </div>
    """
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Outfit Match Analysis</title>
        <style>
            body {{ 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                max-width: 1000px; 
                margin: 0 auto; 
                padding: 20px;
                background-color: #f9f9f9;
                color: #333;
            }}
            .container {{
                padding: 20px;
            }}
            .header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 30px;
            }}
            h1, h2, h3 {{ 
                color: #2c3e50;
            }}
            h1 {{ 
                text-align: center;
                margin-bottom: 30px;
            }}
            .back-btn {{
                display: inline-block;
                padding: 10px 15px;
                background-color: #3498db;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                font-weight: 500;
                transition: all 0.3s ease;
            }}
            .back-btn:hover {{
                background-color: #2980b9;
                box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            }}
            .images-container {{
                display: flex;
                gap: 20px;
                margin-bottom: 30px;
            }}
            .image-box {{
                flex: 1;
                background-color: white;
                border-radius: 8px;
                box-shadow: 0 3px 10px rgba(0,0,0,0.1);
                padding: 15px;
                text-align: center;
            }}
            .image-box h3 {{
                margin-top: 0;
                color: #3498db;
            }}
            .image-box img {{
                max-width: 100%;
                max-height: 400px;
                object-fit: contain;
                border-radius: 5px;
            }}
            .score-overview {{
                background-color: white;
                border-radius: 8px;
                box-shadow: 0 3px 10px rgba(0,0,0,0.1);
                padding: 25px;
                margin-bottom: 30px;
                text-align: center;
                position: relative;
            }}
            .score-circle {{
                width: 150px;
                height: 150px;
                border-radius: 50%;
                margin: 0 auto 20px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 36px;
                font-weight: bold;
                color: white;
                position: relative;
            }}
            .score-label {{
                font-size: 18px;
                margin-top: 15px;
                font-weight: 500;
            }}
            .analysis-items {{
                margin-bottom: 30px;
            }}
            .analysis-item {{
                background-color: white;
                padding: 20px;
                margin-bottom: 15px;
                border-radius: 8px;
                box-shadow: 0 3px 10px rgba(0,0,0,0.1);
            }}
            .analysis-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 10px;
            }}
            .analysis-header h3 {{
                margin: 0;
            }}
            .score-indicator {{
                font-weight: bold;
                padding: 5px 10px;
                border-radius: 20px;
                color: white;
            }}
            .score-bar-container {{
                height: 10px;
                background-color: #eee;
                border-radius: 5px;
                margin-bottom: 15px;
                overflow: hidden;
            }}
            .score-bar {{
                height: 100%;
                border-radius: 5px;
            }}
            .excellent {{
                background-color: #27ae60;
            }}
            .good {{
                background-color: #2980b9;
            }}
            .average {{
                background-color: #f39c12;
            }}
            .poor {{
                background-color: #e74c3c;
            }}
            .analysis-text {{
                margin-top: 15px;
                line-height: 1.5;
            }}
            .suggestions-container {{
                background-color: white;
                border-radius: 8px;
                box-shadow: 0 3px 10px rgba(0,0,0,0.1);
                padding: 20px;
                margin-bottom: 30px;
            }}
            .suggestions-container h3 {{
                margin-top: 0;
                margin-bottom: 15px;
                color: #3498db;
            }}
            .suggestions-list {{
                list-style-type: none;
                padding: 0;
            }}
            .suggestions-list li {{
                padding: 10px 0;
                border-bottom: 1px solid #eee;
                display: flex;
                align-items: flex-start;
            }}
            .suggestions-list li:last-child {{
                border-bottom: none;
            }}
            .suggestion-icon {{
                margin-right: 10px;
                font-style: normal;
            }}
            .metadata {{
                font-size: 0.9em;
                color: #666;
                margin-top: 30px;
                padding: 15px;
                border-top: 1px solid #ddd;
                background-color: #f1f1f1;
                border-radius: 5px;
            }}
            .analysis-explanation {{
                background-color: #f8f9fa;
                border-left: 4px solid #3498db;
                padding: 15px;
                margin-bottom: 20px;
                border-radius: 0 5px 5px 0;
            }}
            .analysis-explanation h3 {{
                margin-top: 0;
                color: #3498db;
            }}
            .analysis-explanation p {{
                margin: 10px 0;
                line-height: 1.5;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Outfit Match Analysis</h1>
                <a href="/" class="back-btn">Back to Upload</a>
            </div>
            
            <div class="images-container">
                <div class="image-box">
                    <h3>Topwear</h3>
                    <img src="{topwear_img}" alt="Topwear Image">
                </div>
                <div class="image-box">
                    <h3>Bottomwear</h3>
                    <img src="{bottomwear_img}" alt="Bottomwear Image">
                </div>
            </div>
            
            <div class="score-overview">
                <div class="score-circle {
                    'excellent' if match_score >= 80 else
                    'good' if match_score >= 65 else
                    'average' if match_score >= 50 else
                    'poor'
                }">
                    {match_score}
                </div>
                <div class="score-label">
                    {
                    'Excellent Match!' if match_score >= 80 else
                    'Good Match' if match_score >= 65 else
                    'Average Compatibility' if match_score >= 50 else
                    'Poor Match'
                    }
                </div>
            </div>
            
            {color_analysis_explanation}
            
            <div class="analysis-items">
                <h2>Detailed Analysis</h2>
                {analysis_items_html}
            </div>
            
            <div class="suggestions-container">
                {suggestions_html}
            </div>
            
            <div class="metadata">
                <p><strong>Processing Time:</strong> {processing_time:.2f} seconds</p>
                <p><strong>Timestamp:</strong> {timestamp}</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html

class SearchRequest(BaseModel):
    query: str

@app.post("/text2image")
async def text2image_page(request: SearchRequest):
    """Text to Image search page"""
    try:
        async with httpx.AsyncClient() as client:
            # Process the text2image request
            image_data = await process_text2image(client, request.query)
            
            # Return the image directly
            return StreamingResponse(io.BytesIO(image_data), media_type="image/jpeg")
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error in text2image processing: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing text2image request: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=9000, log_level="info")

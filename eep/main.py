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
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse, RedirectResponse
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
            <div class="tab" onclick="showTab('elegance')">Elegance Advisor</div>
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
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            services_status = {
                "detection": str(results[0] == True),
                "style": str(results[1] == True),
                "feature": str(results[2] == True),
                "virtual_tryon": str(results[3] == True),
                "elegance": str(results[4] == True),
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
    # Generate a unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    file_extension = os.path.splitext(filename)[1].lower()
    safe_filename = f"{timestamp}_{unique_id}{file_extension}"
    
    # Create full path
    file_path = os.path.join(UPLOAD_FOLDER, safe_filename)
    
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
        <div class="detection-box">
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
        </div>
        '''
    
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
            "details": tryon_result["details"]
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
    model_image_data: str, 
    top_image_data: Optional[str] = None,
    bottom_image_data: Optional[str] = None,
    mode: str = "quality"
) -> Dict:
    """Process multi-garment try-on request through the Virtual Try-On IEP"""
    try:
        payload = {
            "model_image_data": model_image_data,
            "top_image_data": top_image_data,
            "bottom_image_data": bottom_image_data,
            "mode": mode
        }
        
        response = await client.post(
            f"{VIRTUAL_TRYON_SERVICE_URL}/tryon/multi",
            json=payload,
            timeout=float(SERVICE_TIMEOUT * 2)  # Double timeout for multi-garment
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=9000, log_level="info")

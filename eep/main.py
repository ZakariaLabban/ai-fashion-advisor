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
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse, RedirectResponse, StreamingResponse, PlainTextResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union, Tuple
import httpx
from PIL import Image
import aiofiles
import json
import traceback
# Import Prometheus libraries
from prometheus_client import Counter, Histogram, Gauge, Summary, generate_latest

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

# Define Prometheus metrics
API_REQUESTS = Counter(
    'eep_api_requests_total', 
    'Total number of API requests processed',
    ['endpoint']
)
API_ERRORS = Counter(
    'eep_api_errors_total', 
    'Total number of API errors',
    ['endpoint', 'status_code']
)
API_PROCESSING_TIME = Histogram(
    'eep_processing_seconds', 
    'Time spent processing API requests',
    ['endpoint'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0]
)
DETECTION_ITEMS = Counter(
    'eep_detection_items_total',
    'Total number of items detected',
    ['class_name']
)
STYLE_COUNTS = Counter(
    'eep_styles_detected_total',
    'Total number of styles detected',
    ['style_name']
)
RECOMMENDATION_REQUESTS = Counter(
    'eep_recommendation_requests_total',
    'Total number of recommendation requests',
    ['operation', 'item_type']
)
VIRTUAL_TRYON_REQUESTS = Counter(
    'eep_virtual_tryon_requests_total',
    'Total number of virtual try-on requests',
    ['mode']
)
SERVICE_CALLS = Counter(
    'eep_service_calls_total',
    'Total number of internal service calls',
    ['service']
)
SERVICE_ERRORS = Counter(
    'eep_service_errors_total',
    'Total number of internal service errors',
    ['service']
)
SERVICE_RESPONSE_TIME = Histogram(
    'eep_service_response_seconds',
    'Time spent waiting for internal service responses',
    ['service'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
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
PPL_DETECTOR_SERVICE_URL = os.getenv("PPL_DETECTOR_SERVICE_URL", "http://ppl-detector-iep:8009")

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
    people_warning: Optional[str] = None

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
            <p class="info-text">Describe the clothing item you're looking for, and we'll find matching images from our fashion dataset.</p>
            <div id="text2image-form-container">
                <div class="form-group">
                    <label for="text-query">What are you looking for?</label>
                    <input type="text" id="text-query" placeholder="e.g., blue floral summer dress, vintage leather jacket, etc." class="file-input">
                </div>
                <div class="info-text" style="margin-bottom: 10px; color: #666;">
                    <strong>Examples of good queries:</strong> red midi dress, blue denim jacket, floral print blouse, striped t-shirt, black leather boots
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
            <div id="text2image-error" style="margin-top: 30px; text-align: center; display: none;">
                <div style="padding: 20px; background-color: #f8d7da; border-radius: 8px; color: #721c24; max-width: 600px; margin: 0 auto;">
                    <h3 id="error-title" style="margin-top: 0;">Error</h3>
                    <p id="error-message">An error occurred during the search.</p>
                    <div id="error-suggestions" style="margin-top: 15px; background-color: #f8f9fa; padding: 10px; border-radius: 5px;">
                        <p><strong>Suggestions:</strong></p>
                        <ul style="text-align: left; margin: 5px 0 0 0; padding-left: 20px;">
                            <li>Make sure your query is about clothing items</li>
                            <li>Be specific about colors, styles, or garment types</li>
                            <li>Keep queries short and focused</li>
                            <li>Try using fashion terminology</li>
                        </ul>
                    </div>
                </div>
            </div>
            <script>
                document.addEventListener('DOMContentLoaded', function() {
                    const searchButton = document.getElementById('search-button');
                    const textQuery = document.getElementById('text-query');
                    const resultContainer = document.getElementById('text2image-result');
                    const errorContainer = document.getElementById('text2image-error');
                    const resultImage = document.getElementById('result-image');
                    const noResultsMessage = document.getElementById('no-results-message');
                    const errorTitle = document.getElementById('error-title');
                    const errorMessage = document.getElementById('error-message');
                    const errorSuggestions = document.getElementById('error-suggestions');
                    
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
                        errorContainer.style.display = 'none';
                        noResultsMessage.style.display = 'none';
                        resultImage.style.display = 'block';
                        
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
                            
                            if (response.ok && response.headers.get('content-type').includes('image')) {
                                return {
                                    type: 'image',
                                    data: response.blob()
                                };
                            } else {
                                return response.json().then(data => ({
                                    type: 'error',
                                    data: data,
                                    status: response.status
                                }));
                            }
                        })
                        .then(result => {
                            if (result.type === 'image') {
                                // Display the image
                                result.data.then(blob => {
                                    resultImage.src = URL.createObjectURL(blob);
                                    resultContainer.style.display = 'block';
                                });
                            } else {
                                // Show appropriate error message
                                const error = result.data;
                                
                                if (error.error === 'not_clothing_related') {
                                    // Not clothing related
                                    errorTitle.textContent = 'Not Fashion Related';
                                    errorMessage.textContent = error.message || 'Your query does not appear to be related to clothing or fashion. Please try a fashion-related query.';
                                    
                                    // Show specific suggestions for non-clothing queries
                                    errorSuggestions.innerHTML = `
                                        <p><strong>Try queries like:</strong></p>
                                        <ul style="text-align: left; margin: 5px 0 0 0; padding-left: 20px;">
                                            <li>"red midi dress"</li>
                                            <li>"blue denim jacket"</li>
                                            <li>"black leather boots"</li>
                                            <li>"floral print blouse"</li>
                                            <li>"striped t-shirt"</li>
                                        </ul>
                                    `;
                                } else if (result.status === 404) {
                                    // No results found
                                    errorTitle.textContent = 'No Results Found';
                                    errorMessage.textContent = error.message || 'No matching fashion items found for your query. Please try a different search.';
                                    
                                    // Show suggestions for no results
                                    errorSuggestions.innerHTML = `
                                        <p><strong>Suggestions:</strong></p>
                                        <ul style="text-align: left; margin: 5px 0 0 0; padding-left: 20px;">
                                            <li>Try more general terms (e.g., "dress" instead of "evening gown")</li>
                                            <li>Check for typos in your query</li>
                                            <li>Use common colors (red, blue, black, etc.)</li>
                                            <li>Use basic clothing terms (shirt, pants, dress, etc.)</li>
                                        </ul>
                                    `;
                                } else {
                                    // Other error
                                    errorTitle.textContent = 'Search Error';
                                    errorMessage.textContent = error.message || 'An error occurred during the search. Please try again.';
                                    
                                    // General suggestions
                                    errorSuggestions.innerHTML = `
                                        <p><strong>Suggestions:</strong></p>
                                        <ul style="text-align: left; margin: 5px 0 0 0; padding-left: 20px;">
                                            <li>Try again in a few moments</li>
                                            <li>Use simpler search terms</li>
                                            <li>Make sure your query is about clothing items</li>
                                        </ul>
                                    `;
                                }
                                
                                errorContainer.style.display = 'block';
                            }
                        })
                        .catch(error => {
                            console.error('Error:', error);
                            searchButton.disabled = false;
                            searchButton.textContent = 'Find Fashion';
                            
                            errorTitle.textContent = 'Connection Error';
                            errorMessage.textContent = 'There was a problem connecting to the search service. Please try again later.';
                            errorSuggestions.innerHTML = `
                                <p><strong>Suggestions:</strong></p>
                                <ul style="text-align: left; margin: 5px 0 0 0; padding-left: 20px;">
                                    <li>Check your internet connection</li>
                                    <li>Refresh the page and try again</li>
                                    <li>Try again in a few minutes</li>
                                </ul>
                            `;
                            errorContainer.style.display = 'block';
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
    """Health check endpoint."""
    return {"status": "healthy", "message": "EEP service running"}

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return PlainTextResponse(generate_latest(), media_type="text/plain; version=0.0.4; charset=utf-8")

@app.get("/api/analyze/health")
async def analyze_health_check():
    """Specific health check for analyze endpoint"""
    return {"status": "healthy", "message": "Analyze endpoint ready"}

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
                check_iep_health(client, f"{PPL_DETECTOR_SERVICE_URL}/health", "People Detector IEP"),
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
                "ppl_detector": str(results[8] == True),
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
    """Process image detection using the detection IEP service."""
    # Track service calls
    SERVICE_CALLS.labels(service="detection-iep").inc()
    
    start_time = time.time()
    try:
        # Prepare multipart file upload
        files = {"file": ("image.jpg", image_data, "image/jpeg")}
        # Include crops for further processing
        data = {"include_crops": "true"}
        
        # Call the detection service
        resp = await client.post(
            f"{DETECTION_SERVICE_URL}/detect", 
            files=files,
            data=data,
            timeout=SERVICE_TIMEOUT
        )
        
        # Record response time
        SERVICE_RESPONSE_TIME.labels(service="detection-iep").observe(time.time() - start_time)
        
        if resp.status_code != 200:
            SERVICE_ERRORS.labels(service="detection-iep").inc()
            logger.error(f"Error from detection service: {resp.status_code} {resp.text}")
            return []
            
        detection_result = resp.json()
        
        # Count detected items
        for detection in detection_result.get("detections", []):
            DETECTION_ITEMS.labels(class_name=detection.get("class_name", "unknown")).inc()
            
        return detection_result.get("detections", [])
    
    except Exception as e:
        # Track service errors
        SERVICE_ERRORS.labels(service="detection-iep").inc()
        
        logger.error(f"Error calling detection service: {e}")
        return []

async def process_style(client: httpx.AsyncClient, image_data: bytes, request_id: str) -> List[Dict]:
    """Process image style classification using the style IEP service."""
    # Track service calls
    SERVICE_CALLS.labels(service="style-iep").inc()
    
    start_time = time.time()
    try:
        # Prepare multipart file upload
        files = {"file": ("image.jpg", image_data, "image/jpeg")}
        
        # Call the style service
        resp = await client.post(
            f"{STYLE_SERVICE_URL}/classify", 
            files=files,
            timeout=SERVICE_TIMEOUT
        )
        
        # Record response time
        SERVICE_RESPONSE_TIME.labels(service="style-iep").observe(time.time() - start_time)
        
        if resp.status_code != 200:
            SERVICE_ERRORS.labels(service="style-iep").inc()
            logger.error(f"Error from style service: {resp.status_code} {resp.text}")
            return []
            
        style_result = resp.json()
        
        # Count detected styles
        for style in style_result.get("styles", []):
            STYLE_COUNTS.labels(style_name=style.get("style_name", "unknown")).inc()
            
        return style_result.get("styles", [])
    
    except Exception as e:
        # Track service errors
        SERVICE_ERRORS.labels(service="style-iep").inc()
        
        logger.error(f"Error calling style service: {e}")
        return []

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

async def check_people_in_image(client: httpx.AsyncClient, image_contents: bytes, filename: str) -> tuple[int, Optional[str]]:
    """
    Checks how many people are in an image and returns a warning message if there are multiple.
    
    Args:
        client: HTTP client
        image_contents: Image file contents
        filename: Name of the image file
    
    Returns:
        Tuple of (person_count, warning_message) where warning_message is None if no warning needed
    """
    try:
        files = {"file": (filename, image_contents, "image/jpeg")}
        
        response = await client.post(
            f"{PPL_DETECTOR_SERVICE_URL}/count_persons",
            files=files,
            timeout=float(SERVICE_TIMEOUT)
        )
        
        if response.status_code != 200:
            logger.error(f"People counting failed for {filename}: {response.text}")
            return (0, None)  # Return 0 if service fails, no warning
        
        result = response.json()
        person_count = result.get("person_count", 0)
        
        # Generate warning message if more than one person
        warning_message = None
        if person_count > 1:
            warning_message = "We've detected multiple people in your image. Our fashion analysis services perform best with images containing a single person. The analysis will continue, but for optimal results, consider using images with just one person."
        
        return (person_count, warning_message)
    
    except Exception as e:
        logger.error(f"Error counting people in image {filename}: {e}")
        return (0, None)  # On error, assume no people and don't show warning

@app.post("/analyze")
async def analyze_image(request: Request, file: UploadFile = File(...)):
    """Web endpoint for analyzing clothing in an image."""
    # Track API request
    API_REQUESTS.labels(endpoint="/analyze").inc()
    
    start_time = time.time()
    
    try:
        # Generate request ID
        request_id = str(uuid.uuid4())
        logger.info(f"[{request_id}] Starting analysis for file: {file.filename}")
        
        # Read uploaded file
        contents = await file.read()
        
        # Save the original image
        image_path = await save_uploaded_image(contents, file.filename)
        relative_image_path = f"/static/uploads/{os.path.basename(image_path)}"
        
        async with httpx.AsyncClient() as client:
            # Check for multiple people in the image
            person_count, warning = await check_people_in_image(client, contents, file.filename)
            if warning:
                logger.info(f"[{request_id}] Multiple people detected in image: {person_count} people")
            
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
            API_PROCESSING_TIME.labels(endpoint="/analyze").observe(processing_time)
            
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
                "timestamp": datetime.now().isoformat(),
                "people_warning": warning
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
                
                # Add warning about multiple people if applicable
                response_dict = response.dict()
                if warning:
                    response_dict["people_warning"] = warning
                
                # Return as a regular dict
                return response_dict
            
            # For web form submissions, generate HTML directly
            html_content = generate_result_html(
                request_id=request_id,
                original_img=relative_image_path,
                annotated_img=annotated_path,
                detections=detections,
                styles=styles,
                processing_time=processing_time,
                timestamp=datetime.now().isoformat(),
                people_warning=warning
            )
            
            return HTMLResponse(content=html_content, status_code=200)
    
    except Exception as e:
        # Track API errors
        API_ERRORS.labels(endpoint="/analyze", status_code=500).inc()
        
        logger.error(f"Error during image analysis: {e}")
        logger.error(traceback.format_exc())
        error_html = f"""
        <html>
            <head><title>Error</title></head>
            <body>
                <h1>Error Processing Image</h1>
                <p>Sorry, an error occurred: {str(e)}</p>
                <a href="/">Back to Home</a>
            </body>
        </html>
        """
        return HTMLResponse(content=error_html, status_code=500)

@app.post("/api/analyze")
async def api_analyze_image(file: UploadFile = File(...)):
    """API endpoint for analyzing clothing in an image."""
    # Track API request
    API_REQUESTS.labels(endpoint="/api/analyze").inc()
    
    start_time = time.time()
    
    try:
        # Generate request ID
        request_id = str(uuid.uuid4())
        
        # Read the uploaded file
        contents = await file.read()
        
        # Save the original file
        filename = f"{request_id}_{file.filename}"
        image_path = await save_uploaded_image(contents, filename)
        
        # Process the image
        async with httpx.AsyncClient() as client:
            # Process with IEP
            form_data = {
                "include_crops": str(include_crops).lower(),
            }
            
            if confidence is not None:
                form_data["confidence"] = str(confidence)
            
            files = {"file": (file.filename, contents, file.content_type)}
            
            response = await client.post(
                f"{PPL_DETECTOR_SERVICE_URL}/detect",
                files=files,
                data=form_data
            )
            
            if response.status_code != 200:
                logger.error(f"People detection failed: {response.text}")
                raise HTTPException(status_code=response.status_code, detail="People detection failed")
            
            # Get the detection results
            detection_results = response.json()
            
            # Measure processing time
            processing_time = time.time() - start_time
            
            # Include total processing time
            detection_results["total_processing_time"] = processing_time
            
            return detection_results
    
    except Exception as e:
        logger.error(f"Error in people detection: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

@app.post("/count_people", tags=["People Detection"])
async def count_people(
    file: UploadFile = File(...),
    confidence: Optional[float] = Form(None)
):
    """
    Count the number of people in the uploaded image.
    
    - **file**: The image file to process
    - **confidence**: Optional confidence threshold override
    """
    try:
        contents = await file.read()
        
        # Process with IEP
        form_data = {}
        if confidence is not None:
            form_data["confidence"] = str(confidence)
        
        files = {"file": (file.filename, contents, file.content_type)}
        
        async with httpx.AsyncClient(timeout=SERVICE_TIMEOUT) as client:
            response = await client.post(
                f"{PPL_DETECTOR_SERVICE_URL}/count_persons",
                files=files,
                data=form_data
            )
            
            if response.status_code != 200:
                logger.error(f"People counting failed: {response.text}")
                raise HTTPException(status_code=response.status_code, detail="People counting failed")
            
            # Return the results
            return response.json()
    
    except Exception as e:
        logger.error(f"Error in people counting: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

async def validate_no_people_in_image(client: httpx.AsyncClient, image_contents: bytes, filename: str) -> tuple[bool, str]:
    """
    Validates that the image contains zero or one person (acceptable for clothing items).
    
    Args:
        client: HTTP client
        image_contents: Image file contents
        filename: Name of the image file
    
    Returns:
        Tuple of (is_valid, message) where is_valid is True if image contains 0 or 1 person,
        and message contains the error message if not valid
    """
    try:
        files = {"file": (filename, image_contents, "image/jpeg")}
        
        response = await client.post(
            f"{PPL_DETECTOR_SERVICE_URL}/count_persons",
            files=files,
            timeout=float(SERVICE_TIMEOUT)
        )
        
        if response.status_code != 200:
            logger.error(f"People counting failed for {filename}: {response.text}")
            return (True, "")  # Allow to proceed if validation fails
        
        result = response.json()
        person_count = result.get("person_count", 0)
        
        if person_count > 1:
            return (False, f"We detected multiple people in your {filename}. Please upload an image with just the clothing item or a single person.")
        
        # If zero or one person, return True (both are acceptable for clothing items)
        return (True, "")
    
    except Exception as e:
        logger.error(f"Error validating person count for {filename}: {e}")
        return (True, "")  # Allow to proceed if validation fails

async def validate_single_person_in_image(client: httpx.AsyncClient, image_contents: bytes, filename: str) -> tuple[bool, str]:
    """
    Validates that the image contains exactly one person.
    
    Args:
        client: HTTP client
        image_contents: Image file contents
        filename: Name of the image file
    
    Returns:
        Tuple of (is_valid, message) where is_valid is True if image contains exactly 1 person,
        and message contains the error message if not valid
    """
    try:
        files = {"file": (filename, image_contents, "image/jpeg")}
        
        response = await client.post(
            f"{PPL_DETECTOR_SERVICE_URL}/count_persons",
            files=files,
            timeout=float(SERVICE_TIMEOUT)
        )
        
        if response.status_code != 200:
            logger.error(f"People counting failed: {response.text}")
            return (False, "Unable to validate the number of people in the image.")
        
        result = response.json()
        person_count = result.get("person_count", 0)
        
        if person_count == 0:
            return (False, "We couldn't detect anyone in your photo. Please provide a clear photo of yourself.")
        elif person_count > 1:
            return (False, "We know you're a social person, but we need a picture of you alone for the virtual try-on to work properly.")
        
        # If exactly one person, return True
        return (True, "")
    
    except Exception as e:
        logger.error(f"Error validating person count: {e}")
        return (False, "Error validating the image. Please try again.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=9000, log_level="info")

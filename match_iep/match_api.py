from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Body, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union
import httpx
import os
import numpy as np
import io
import json
import logging
import math
from PIL import Image
import colorsys
import cv2
from dotenv import load_dotenv
import uvicorn
from datetime import datetime
import asyncio
import time
# Import Prometheus client for metrics
from prometheus_client import Counter, Histogram, Gauge, generate_latest

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Fashion Matching IEP",
    description="Internal Endpoint Processor for evaluating outfit matchability",
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
FEATURE_SERVICE_URL = os.getenv("FEATURE_SERVICE_URL", "http://feature-iep:8003")
STYLE_SERVICE_URL = os.getenv("STYLE_SERVICE_URL", "http://style-iep:8002")

# Timeout for service requests (in seconds)
SERVICE_TIMEOUT = int(os.getenv("SERVICE_TIMEOUT", "30"))

# Define Prometheus metrics
MATCH_REQUESTS = Counter(
    'match_requests_total', 
    'Total number of outfit match requests processed'
)
MATCH_ERRORS = Counter(
    'match_errors_total', 
    'Total number of errors during outfit matching'
)
MATCH_PROCESSING_TIME = Histogram(
    'match_processing_seconds', 
    'Time spent processing outfit match requests',
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
)
MATCH_SCORES = Histogram(
    'match_scores', 
    'Distribution of outfit match scores',
    buckets=[10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
)
COLOR_HARMONY_SCORES = Histogram(
    'color_harmony_scores', 
    'Distribution of color harmony scores',
    buckets=[10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
)
STYLE_CONSISTENCY_SCORES = Histogram(
    'style_consistency_scores', 
    'Distribution of style consistency scores',
    buckets=[10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
)

# Models
class MatchResponse(BaseModel):
    match_score: int
    analysis: Dict[str, Dict[str, Union[int, str]]]
    suggestions: List[str]
    alternative_pairings: Optional[List[Dict[str, Any]]] = None

class ColorAnalysis(BaseModel):
    dominant_colors: List[List[int]]  # RGB values
    color_histogram: Dict[str, float]
    color_family: str

class MatchRequest(BaseModel):
    """Pydantic model for centralized match request with preprocessed data"""
    top_style: str
    bottom_style: str
    top_vector: List[float] = Field(default_factory=list)
    bottom_vector: List[float] = Field(default_factory=list)
    top_histogram: List[float] = Field(default_factory=list)
    bottom_histogram: List[float] = Field(default_factory=list)
    top_detection: Dict[str, Any] = Field(default_factory=dict)
    bottom_detection: Dict[str, Any] = Field(default_factory=dict)

# Utility functions
def extract_dominant_colors(image, n_colors=3):
    """Extract dominant colors from an image using K-means clustering"""
    img = np.array(image)
    pixels = img.reshape(-1, 3)
    
    # Use K-means to find dominant colors
    from sklearn.cluster import KMeans
    kmeans = KMeans(n_clusters=n_colors, n_init=10)
    kmeans.fit(pixels)
    
    # Get colors and their percentages
    colors = kmeans.cluster_centers_.astype(int)
    counts = np.bincount(kmeans.labels_)
    percentages = counts / len(pixels)
    
    # Sort by percentage (highest first)
    sorted_indices = np.argsort(percentages)[::-1]
    dominant_colors = [colors[i].tolist() for i in sorted_indices]
    
    return dominant_colors

def get_color_family(rgb):
    """Determine the color family of an RGB value"""
    r, g, b = rgb
    
    # Check if values are in 0-1 range and convert to 0-255 if needed
    if max(r, g, b) <= 1.0:
        r, g, b = r * 255, g * 255, b * 255
    
    # Convert RGB to HSV
    h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
    
    # Convert hue to degrees (0-360)
    h_degrees = h * 360
    
    # Log for debugging
    logger.info(f"Color RGB: ({r:.1f}, {g:.1f}, {b:.1f}), HSV: ({h_degrees:.1f}°, {s:.2f}, {v:.2f})")
    
    # Determine color family based on HSV
    if s < 0.15 and v > 0.8:
        return "white"
    elif s < 0.15 and v < 0.2:
        return "black"
    elif s < 0.15:
        return "gray"
    elif h_degrees < 30 or h_degrees > 330:
        return "red"
    elif h_degrees < 90:
        return "yellow"
    elif h_degrees < 150:
        return "green"
    elif h_degrees < 210:
        return "cyan"
    elif h_degrees < 270:
        return "blue"
    elif h_degrees < 330:
        return "magenta"
    else:
        return "unknown"

def calculate_color_harmony(top_colors, bottom_colors):
    """Calculate color harmony score between top and bottom"""
    # Extract primary colors
    top_primary = top_colors[0] if top_colors else [0, 0, 0]
    bottom_primary = bottom_colors[0] if bottom_colors else [0, 0, 0]
    
    # Convert to HSV for better color comparison
    top_hsv = colorsys.rgb_to_hsv(top_primary[0]/255, top_primary[1]/255, top_primary[2]/255)
    bottom_hsv = colorsys.rgb_to_hsv(bottom_primary[0]/255, bottom_primary[1]/255, bottom_primary[2]/255)
    
    # Extract hue, saturation, value
    top_h, top_s, top_v = top_hsv
    bottom_h, bottom_s, bottom_v = bottom_hsv
    
    # Convert hue to degrees (0-360)
    top_h_deg = top_h * 360
    bottom_h_deg = bottom_h * 360
    
    # Calculate hue difference (0-180)
    hue_diff = min(abs(top_h_deg - bottom_h_deg), 360 - abs(top_h_deg - bottom_h_deg))
    
    # Calculate harmony based on color wheel theory
    # Complementary colors: ~180 degrees apart
    # Analogous colors: ~30 degrees apart
    # Monochromatic: similar hue, different saturation/value
    
    # Harmony scores (0-100)
    complementary_score = 100 - abs(hue_diff - 180) * 100/180
    analogous_score = 100 - min(hue_diff, 60) * 100/60
    monochromatic_score = 100 - hue_diff * 100/360
    
    # For neutral colors (low saturation), different rules apply
    is_top_neutral = top_s < 0.2
    is_bottom_neutral = bottom_s < 0.2
    
    if is_top_neutral and is_bottom_neutral:
        # Two neutrals - check contrast
        contrast_diff = abs(top_v - bottom_v)
        
        # Special case: Very low contrast between neutrals - increase score
        if contrast_diff < 0.1:  # For cases with "0% contrast" or very low contrast
            neutral_score = 85  # Increased from the original calculation to favor this case
        else:
            neutral_score = contrast_diff * 100  # Higher contrast is better for neutrals
    elif is_top_neutral or is_bottom_neutral:
        # One neutral with a color usually works well
        neutral_score = 80
    else:
        neutral_score = 0  # Not using neutral scoring
    
    # Brightness contrast
    brightness_diff = abs(top_v - bottom_v)
    brightness_score = max(50, min(100, brightness_diff * 200))  # Some contrast is good
    
    # Calculate final harmony score
    if is_top_neutral and is_bottom_neutral:
        if brightness_diff < 0.1:  # For the very low contrast case
            harmony_score = neutral_score  # Use the increased neutral score directly
        else:
            harmony_score = 0.6 * neutral_score + 0.4 * brightness_score
    elif is_top_neutral or is_bottom_neutral:
        # Check for complementary, analogous, or monochromatic
        if 150 <= hue_diff <= 210:  # Near complementary
            harmony_score = 0.6 * complementary_score + 0.4 * brightness_score
        elif hue_diff <= 30:  # Near analogous or monochromatic
            harmony_score = 0.7 * analogous_score + 0.3 * brightness_score
        else:
            # Other combinations - use a weighted average
            harmony_score = 0.4 * complementary_score + 0.3 * analogous_score + 0.3 * brightness_score
    
    # Ensure score is 0-100
    harmony_score = max(0, min(100, harmony_score))
    
    # Generate analysis text
    if is_top_neutral and is_bottom_neutral:
        if brightness_diff < 0.1:
            color_analysis = f"Elegant neutral-on-neutral pairing creating a sophisticated monochromatic look."
        else:
            color_analysis = f"Neutral color pairing with {brightness_diff:.0%} contrast."
    elif is_top_neutral:
        color_analysis = f"Neutral top with {get_color_family(bottom_primary)} bottom creates a balanced look."
    elif is_bottom_neutral:
        color_analysis = f"{get_color_family(top_primary)} top with neutral bottom creates a focused outfit."
    elif 150 <= hue_diff <= 210:
        color_analysis = f"Complementary color pairing between {get_color_family(top_primary)} and {get_color_family(bottom_primary)}."
    elif hue_diff <= 30:
        color_analysis = f"Harmonious {get_color_family(top_primary)}/{get_color_family(bottom_primary)} analogous color scheme."
    else:
        color_analysis = f"{get_color_family(top_primary)} top with {get_color_family(bottom_primary)} bottom has moderate color contrast."
    
    return round(harmony_score), color_analysis

def evaluate_style_consistency(top_style, bottom_style):
    """Evaluate style consistency between top and bottom wear"""
    # Style compatibility matrix (simplified)
    # Score from 0-100
    compatibility_matrix = {
        "casual": {
            "casual": 95,
            "formal": 50,       # Increased (was 30)
            "sports": 80,       # Increased (was 70)
            "ethnic": 70,       # Increased (was 60)
            "business": 60,     # Increased (was 40)
            "party": 75,        # Increased (was 60)
            "streetwear": 90    # New style
        },
        "formal": {
            "casual": 50,       # Increased (was 30)
            "formal": 95,
            "sports": 30,       # Increased (was 10)
            "ethnic": 65,       # Increased (was 50)
            "business": 90,     # Increased (was 85)
            "party": 80,        # Increased (was 70)
            "streetwear": 45    # New style
        },
        "sports": {
            "casual": 80,       # Increased (was 70)
            "formal": 30,       # Increased (was 10)
            "sports": 95,
            "ethnic": 40,       # Increased (was 20)
            "business": 35,     # Increased (was 15)
            "party": 50,        # Increased (was 30)
            "streetwear": 85    # New style
        },
        "ethnic": {
            "casual": 70,       # Increased (was 60)
            "formal": 65,       # Increased (was 50)
            "sports": 40,       # Increased (was 20)
            "ethnic": 95,
            "business": 60,     # Increased (was 45)
            "party": 85,        # Increased (was 75)
            "streetwear": 65    # New style
        },
        "business": {
            "casual": 60,       # Increased (was 40)
            "formal": 90,       # Increased (was 85)
            "sports": 35,       # Increased (was 15)
            "ethnic": 60,       # Increased (was 45)
            "business": 95,
            "party": 70,        # Increased (was 60)
            "streetwear": 50    # New style
        },
        "party": {
            "casual": 75,       # Increased (was 60)
            "formal": 80,       # Increased (was 70)
            "sports": 50,       # Increased (was 30)
            "ethnic": 85,       # Increased (was 75)
            "business": 70,     # Increased (was 60)
            "party": 95,
            "streetwear": 80    # New style
        },
        "streetwear": {         # New style category
            "casual": 90,
            "formal": 45,
            "sports": 85,
            "ethnic": 65,
            "business": 50,
            "party": 80,
            "streetwear": 95
        }
    }
    
    # Default score for unknown styles - more lenient default
    default_score = 60  # Increased from 50
    
    # Get compatibility score
    score = compatibility_matrix.get(top_style, {}).get(bottom_style, default_score)
    
    # Generate analysis text - more positive language
    if score >= 85:
        analysis = f"Excellent {top_style}-{bottom_style} style matching."
    elif score >= 70:
        analysis = f"Good style consistency between {top_style} top and {bottom_style} bottom."
    elif score >= 50:
        analysis = f"{top_style.capitalize()} top and {bottom_style} bottom create an interesting style contrast."  # More positive
    else:
        analysis = f"{top_style.capitalize()} top and {bottom_style} bottom have distinctly different styles that create a bold fashion statement."  # Much more positive
    
    return score, analysis

def analyze_occasion_appropriateness(top_style, bottom_style, top_color_family, bottom_color_family):
    """Analyze occasion appropriateness based on styles and colors"""
    # Map styles to appropriate occasions
    occasion_map = {
        "casual": ["everyday", "weekend", "leisure"],
        "formal": ["wedding", "ceremony", "gala"],
        "sports": ["gym", "outdoor", "activity"],
        "ethnic": ["cultural events", "festival", "celebration"],
        "business": ["office", "meeting", "interview"],
        "party": ["evening out", "celebration", "social gathering"]
    }
    
    # Find common occasions
    top_occasions = occasion_map.get(top_style, ["everyday"])
    bottom_occasions = occasion_map.get(bottom_style, ["everyday"])
    common_occasions = set(top_occasions).intersection(set(bottom_occasions))
    
    # Calculate score based on occasion overlap and color appropriateness
    if common_occasions:
        base_score = 80
    else:
        base_score = 50
    
    # Adjust for color appropriateness
    neutral_colors = ["black", "white", "gray", "navy"]
    is_top_neutral = top_color_family in neutral_colors
    is_bottom_neutral = bottom_color_family in neutral_colors
    
    if is_top_neutral and is_bottom_neutral:
        # Neutral combinations work for most occasions
        color_adjustment = +10
        color_note = "Neutral color palette suitable for various occasions."
    elif is_top_neutral or is_bottom_neutral:
        # One neutral makes the outfit more versatile
        color_adjustment = +5
        color_note = "Partially neutral color scheme offers good versatility."
    else:
        # Bold colors may limit occasion flexibility
        color_adjustment = -5
        color_note = "Colorful combination may limit occasion versatility."
    
    # Certain style combinations have specific occasion notes
    if top_style == "business" and bottom_style == "business":
        occasion_note = "Perfect for professional workplace environments."
        occasion_score = 95
    elif (top_style == "casual" and bottom_style == "casual"):
        occasion_note = "Ideal for everyday casual wear and relaxed settings."
        occasion_score = 90
    elif (top_style == "formal" and bottom_style == "formal"):
        occasion_note = "Suitable for formal events and celebrations."
        occasion_score = 95
    elif (top_style in ["business", "formal"] and bottom_style in ["business", "formal"]):
        occasion_note = "Appropriate for professional and semi-formal settings."
        occasion_score = 85
    else:
        # Use the base score with color adjustment
        occasion_score = base_score + color_adjustment
        if common_occasions:
            occasion_list = ", ".join(common_occasions)
            occasion_note = f"Best suited for {occasion_list}. {color_note}"
        else:
            occasion_note = f"Limited occasion compatibility. {color_note}"
    
    # Ensure score is 0-100
    occasion_score = max(0, min(100, occasion_score))
    
    return round(occasion_score), occasion_note

def calculate_trend_alignment(top_style, bottom_style):
    """Calculate how well the outfit aligns with current trends"""
    # This would ideally use up-to-date trend data
    # For now, using a simplified approach based on style combinations
    
    # Current trend score map (this would normally be updated regularly)
    # Values represent trendiness of combinations (0-100)
    trend_matrix = {
        "casual+casual": 85,        # Casual coordinates are current
        "casual+sports": 90,        # Athleisure is trendy
        "business+casual": 80,      # Business casual is relevant
        "formal+formal": 75,        # Classic formal is timeless
        "ethnic+ethnic": 80,        # Cultural authenticity is valued
        "party+party": 85,          # Party-specific outfits are cyclical
        "sports+sports": 90,        # Athleisure dominates
        "business+formal": 70,      # Traditional professional attire
        "casual+ethnic": 85,        # Fusion/global styles are trending
        "party+casual": 80          # High-low mix is popular
        # Default for other combinations is calculated below
    }
    
    # Get trend score
    combo_key = f"{top_style}+{bottom_style}"
    reverse_combo_key = f"{bottom_style}+{top_style}"
    
    if combo_key in trend_matrix:
        trend_score = trend_matrix[combo_key]
    elif reverse_combo_key in trend_matrix:
        trend_score = trend_matrix[reverse_combo_key]
    else:
        # Calculate average trend relevance for unknown combinations
        style_trend_scores = {
            "casual": 85,     # Always relevant
            "sports": 90,     # Currently trending
            "business": 75,   # Steady
            "formal": 70,     # Classic but less daily wear
            "ethnic": 80,     # Cultural appreciation trending
            "party": 80       # Cyclical
        }
        
        top_trend = style_trend_scores.get(top_style, 75)
        bottom_trend = style_trend_scores.get(bottom_style, 75)
        trend_score = (top_trend + bottom_trend) / 2
    
    # Generate analysis text
    if trend_score >= 85:
        trend_analysis = f"Very current {top_style}-{bottom_style} combination aligns with latest trends."
    elif trend_score >= 75:
        trend_analysis = f"Fashionable pairing with contemporary appeal."
    elif trend_score >= 65:
        trend_analysis = f"Classic combination with enduring style."
    else:
        trend_analysis = f"Traditional pairing that prioritizes convention over trends."
    
    return round(trend_score), trend_analysis

def generate_suggestions(analysis_results):
    """Generate outfit improvement suggestions based on analysis"""
    suggestions = []
    
    # Extract scores for reference
    color_score = analysis_results["color_harmony"]["score"]
    style_score = analysis_results["style_consistency"]["score"]
    occasion_score = analysis_results["occasion_appropriateness"]["score"]
    
    # New metrics if available
    feature_score = analysis_results.get("feature_match", {}).get("score", 0)
    histogram_score = analysis_results.get("color_histogram_match", {}).get("score", 0)
    
    # Color harmony suggestions (K-means)
    if color_score < 70:
        suggestions.append("For even better harmony, explore items with complementary or analogous colors to enhance your look.")
    
    # Style suggestions - more positive framing
    if style_score < 70:
        suggestions.append("This unique style mixture creates an interesting contrast - consider adding a transitional accessory to bridge the styles.")
    
    # Add suggestions based on feature match - more constructive
    if feature_score > 0 and feature_score < 65:
        suggestions.append("These pieces have distinctive visual characteristics - embrace this creative pairing or consider items with similar textures or patterns for a different look.")
    
    # Add suggestions based on color histogram - more positive
    if histogram_score > 0 and histogram_score < 65:
        suggestions.append("The colors in this outfit create a bold statement - for a different vibe, try pieces with more complementary color palettes.")
    
    # Generic suggestions that enhance most outfits - more positive and fashionable
    styling_suggestions = [
        "A statement belt would help tie this look together and add a polished finish.",
        "Accessories like a watch or layered jewelry could elevate this look and express your personal style.",
        "Footwear in a complementary tone would complete this outfit beautifully.",
        "Layering with a jacket or cardigan would add dimension and versatility to this combination.",
        "A scarf or statement necklace could bring this whole outfit together perfectly."
    ]
    
    # Add 1-2 generic styling suggestions
    import random
    random.shuffle(styling_suggestions)
    suggestions.extend(styling_suggestions[:2])
    
    return suggestions[:4]  # Limit to 4 suggestions

async def validate_clothing_types(top_image, bottom_image):
    """
    Validate that images are indeed top and bottom wear and return style classifications
    
    Returns:
        tuple: (valid, error_message, top_style_result, bottom_style_result)
            - valid: Boolean indicating if validation passed
            - error_message: Error message if validation failed, None otherwise
            - top_style_result: Style classification result for top image
            - bottom_style_result: Style classification result for bottom image
    """
    try:
        # Convert images to bytes for API calls
        top_image_bytes = io.BytesIO()
        bottom_image_bytes = io.BytesIO()
        top_image.save(top_image_bytes, format="JPEG")
        bottom_image.save(bottom_image_bytes, format="JPEG")
        top_image_bytes.seek(0)
        bottom_image_bytes.seek(0)
        
        # Call style-iep to classify both images
        async with httpx.AsyncClient() as client:
            # Classify top image
            top_files = {"file": ("top.jpg", top_image_bytes.getvalue(), "image/jpeg")}
            top_response = await client.post(
                f"{STYLE_SERVICE_URL}/classify",
                files=top_files,
                timeout=SERVICE_TIMEOUT
            )
            
            if top_response.status_code != 200:
                logger.error(f"Style IEP validation error for topwear: {top_response.text}")
                return False, "Error validating topwear image", None, None
            
            # Classify bottom image
            bottom_files = {"file": ("bottom.jpg", bottom_image_bytes.getvalue(), "image/jpeg")}
            bottom_response = await client.post(
                f"{STYLE_SERVICE_URL}/classify",
                files=bottom_files,
                timeout=SERVICE_TIMEOUT
            )
            
            if bottom_response.status_code != 200:
                logger.error(f"Style IEP validation error for bottomwear: {bottom_response.text}")
                return False, "Error validating bottomwear image", None, None
            
            # Get results
            top_result = top_response.json()
            bottom_result = bottom_response.json()
            
            # Check if any styles were detected
            if not top_result.get("styles"):
                logger.warning("No style detected in topwear image")
                return False, "Could not detect styles in topwear image. Please ensure it contains visible clothing.", None, None
                
            if not bottom_result.get("styles"):
                logger.warning("No style detected in bottomwear image")
                return False, "Could not detect styles in bottomwear image. Please ensure it contains visible clothing.", None, None
                
            # For now, we're just checking if styles are detected
            # In a more advanced implementation, we could check if the detected garment types 
            # match what we expect (top vs. bottom)
            
            return True, None, top_result, bottom_result
            
    except Exception as e:
        logger.error(f"Error during clothing type validation: {str(e)}")
        return False, f"Validation error: {str(e)}", None, None

async def extract_features(client: httpx.AsyncClient, image_data: bytes, item_name: str):
    """Extract features from an image using feature-iep
    
    Args:
        client: httpx client
        image_data: image bytes
        item_name: name of item (for logging)
        
    Returns:
        dict: feature extraction results including feature vector and color histogram
    """
    try:
        logger.info(f"Sending {item_name} to Feature IEP for feature extraction")
        files = {"file": (f"{item_name}.jpg", image_data, "image/jpeg")}
        
        response = await client.post(
            f"{FEATURE_SERVICE_URL}/extract",
            files=files,
            timeout=SERVICE_TIMEOUT
        )
        
        if response.status_code != 200:
            logger.error(f"Feature IEP error for {item_name}: {response.text}")
            raise HTTPException(status_code=500, detail=f"Feature service error for {item_name}")
        
        result = response.json()
        logger.info(f"Feature IEP response received for {item_name}")
        return result
    except Exception as e:
        logger.error(f"Error extracting features for {item_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Feature extraction error: {str(e)}")

def calculate_cosine_similarity(vector1, vector2):
    """Calculate cosine similarity between two vectors
    
    Args:
        vector1: First vector
        vector2: Second vector
        
    Returns:
        float: cosine similarity value between 0 and 1 (higher is more similar)
    """
    if not vector1 or not vector2:
        return 0.0
        
    # Convert to numpy arrays if they aren't already
    v1 = np.array(vector1)
    v2 = np.array(vector2)
    
    # Handle zero vectors
    if np.all(v1 == 0) or np.all(v2 == 0):
        return 0.0
    
    # Calculate cosine similarity: dot(v1, v2) / (norm(v1) * norm(v2))
    dot_product = np.dot(v1, v2)
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)
    
    similarity = dot_product / (norm_v1 * norm_v2)
    
    # Ensure value is between 0 and 1
    return max(0.0, min(1.0, similarity))

def calculate_euclidean_distance(vector1, vector2, normalize=True):
    """Calculate Euclidean distance between two vectors
    
    Args:
        vector1: First vector
        vector2: Second vector
        normalize: Whether to normalize the result to 0-1 range (1 = identical)
        
    Returns:
        float: normalized distance value between 0 and 1 (higher is more similar)
    """
    if not vector1 or not vector2:
        return 0.0
        
    # Convert to numpy arrays if they aren't already
    v1 = np.array(vector1)
    v2 = np.array(vector2)
    
    # Calculate Euclidean distance
    distance = np.linalg.norm(v1 - v2)
    
    if normalize:
        # For normalization, we need a sensible maximum distance
        # This is a heuristic that can be adjusted based on feature vector properties
        max_distance = np.sqrt(len(v1)) * 2  # Assuming values roughly in range [-1, 1]
        
        # Convert distance to similarity (0 to 1, where 1 means identical)
        similarity = max(0.0, 1.0 - (distance / max_distance))
        return similarity
    
    return distance

def calculate_feature_match_score(top_features, bottom_features):
    """Calculate match score based on feature vectors
    
    This uses cosine similarity as it's better for high-dimensional feature vectors
    
    Args:
        top_features: Feature vector of top item
        bottom_features: Feature vector of bottom item
        
    Returns:
        tuple: (score, analysis_text)
    """
    similarity = calculate_cosine_similarity(top_features, bottom_features)
    
    # Convert to 0-100 score
    score = round(similarity * 100)
    
    # Generate analysis text
    if score >= 85:
        analysis = "Excellent feature compatibility indicating harmonious outfit composition."
    elif score >= 70:
        analysis = "Good feature similarity suggesting compatible style elements."
    elif score >= 50:
        analysis = "Moderate feature compatibility that can work with proper styling."
    else:
        analysis = "Low feature similarity indicating contrasting style elements."
    
    return score, analysis

def calculate_color_histogram_match(top_histogram, bottom_histogram):
    """Calculate match score based on color histograms
    
    For color histograms, we need to consider:
    - Complementary colors (opposite on color wheel) can work well together
    - Very similar colors can work well (monochromatic)
    - Colors with high contrast in value (lightness) often work well
    
    Args:
        top_histogram: Color histogram of top item
        bottom_histogram: Color histogram of bottom item
        
    Returns:
        tuple: (score, analysis_text)
    """
    # Use a weighted combination of metrics
    cosine_sim = calculate_cosine_similarity(top_histogram, bottom_histogram)
    euclidean_sim = calculate_euclidean_distance(top_histogram, bottom_histogram, normalize=True)
    
    # Convert histograms to numpy arrays
    top_hist = np.array(top_histogram)
    bottom_hist = np.array(bottom_histogram)
    
    # Calculate histogram entropy (measure of color diversity)
    top_entropy = -np.sum(top_hist * np.log2(top_hist + 1e-10))
    bottom_entropy = -np.sum(bottom_hist * np.log2(bottom_hist + 1e-10))
    
    # Calculate color contrast
    # For this simple implementation, we'll use the difference in entropy
    # as a proxy for contrast (more diverse colors = more contrast)
    entropy_diff = abs(top_entropy - bottom_entropy)
    normalized_entropy_diff = min(1.0, entropy_diff / 5.0)  # Normalize to [0,1]
    
    # Very high or very low similarity can both be good for different reasons:
    # - High similarity: monochromatic look (good)
    # - Medium similarity: potentially clashing (bad)
    # - Low similarity: potentially complementary (good)
    
    # Calculate a "similarity score" that rewards both high and low similarity
    # (U-shaped function that gives high scores to both very similar and very different colors)
    similarity_score = 1.0 - 4.0 * (cosine_sim - 0.5) * (cosine_sim - 0.5)
    
    # Combine metrics:
    # - Similarity score (higher is better): rewards both match and opposition
    # - Normalized entropy difference (higher is better): rewards contrast
    weighted_score = (0.6 * similarity_score + 0.4 * normalized_entropy_diff) * 100
    score = round(weighted_score)
    
    # Generate analysis text
    if cosine_sim > 0.8:
        analysis = "Harmonious monochromatic color scheme with subtle variations."
    elif cosine_sim < 0.3:
        analysis = "Bold contrasting color combination creating visual interest."
    elif normalized_entropy_diff > 0.7:
        analysis = "Good color contrast between items enhancing visual appeal."
    else:
        analysis = "Moderate color coordination that works with proper styling."
    
    return score, analysis

async def detect_clothing_items(client: httpx.AsyncClient, image_data: bytes, item_name: str):
    """Detect clothing items in an image using detection-iep
    
    Args:
        client: httpx client
        image_data: image bytes
        item_name: name of item (for logging)
        
    Returns:
        dict: detection results
    """
    try:
        logger.info(f"Sending {item_name} to Detection IEP")
        files = {"file": (f"{item_name}.jpg", image_data, "image/jpeg")}
        
        # Send image to detection-iep
        response = await client.post(
            "http://detection-iep:8001/detect",  # Hardcoded URL since it's not in env vars
            files=files,
            timeout=SERVICE_TIMEOUT
        )
        
        if response.status_code != 200:
            logger.error(f"Detection IEP error for {item_name}: {response.text}")
            raise HTTPException(status_code=500, detail=f"Detection service error for {item_name}")
        
        result = response.json()
        logger.info(f"Detection IEP found {len(result.get('detections', []))} items for {item_name}")
        return result
    except Exception as e:
        logger.error(f"Error detecting items for {item_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Detection error: {str(e)}")

def extract_crop_from_detection(image, detection):
    """Extract cropped image from detection bbox
    
    Args:
        image: PIL Image
        detection: Detection with bbox
        
    Returns:
        PIL Image: Cropped image
    """
    try:
        # Extract bbox coordinates
        bbox = detection.get('bbox', [0, 0, 0, 0])
        if len(bbox) != 4:
            logger.warning("Invalid bbox format")
            return None
            
        # Make sure bbox is within image bounds
        width, height = image.size
        x1, y1, x2, y2 = bbox
        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(width, x2)
        y2 = min(height, y2)
        
        # Crop the image
        cropped_img = image.crop((x1, y1, x2, y2))
        return cropped_img
    except Exception as e:
        logger.error(f"Error cropping image: {str(e)}")
        return None

def find_garment_by_class(detections, target_class):
    """Find the highest confidence detection of a specific class
    
    Args:
        detections: List of detections
        target_class: Class name to find
    
    Returns:
        dict: Detection with highest confidence or None if not found
    """
    matching_detections = []
    for detection in detections:
        if detection.get('class_name', '').lower() == target_class.lower():
            matching_detections.append(detection)
    
    if not matching_detections:
        return None
    
    # Sort by confidence (highest first)
    sorted_detections = sorted(
        matching_detections, 
        key=lambda x: float(x.get('confidence', 0)), 
        reverse=True
    )
    
    return sorted_detections[0]

# API Endpoints
@app.get("/")
async def root():
    """Root endpoint with basic service information"""
    return {
        "service": "Fashion Matching IEP",
        "version": "1.0.0",
        "status": "active"
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return PlainTextResponse(generate_latest(), media_type="text/plain; version=0.0.4; charset=utf-8")

@app.post("/match", response_model=MatchResponse)
async def match_outfit(
    topwear: UploadFile = File(...),
    bottomwear: UploadFile = File(...)
):
    """
    Match top and bottom clothing items and evaluate their compatibility.
    """
    # Increment the request counter
    MATCH_REQUESTS.inc()
    
    start_time = time.time()
    try:
        # Process uploaded images
        top_content = await topwear.read()
        bottom_content = await bottomwear.read()
        
        # Convert to PIL images for color extraction
        top_image = Image.open(io.BytesIO(top_content)).convert('RGB')
        bottom_image = Image.open(io.BytesIO(bottom_content)).convert('RGB')
        
        # Initialize variables for the API responses
        top_style_result = None
        bottom_style_result = None
        top_feature_result = None
        bottom_feature_result = None
        top_detection_result = None
        bottom_detection_result = None
        
        # For the specific clothing items
        top_shirt_crop = None
        bottom_pants_crop = None
        
        # Create an HTTP client for API calls
        async with httpx.AsyncClient() as client:
            # STEP 1: Style Classification
            # First validate clothing types and get style classifications
            valid, error_message, top_style_result, bottom_style_result = await validate_clothing_types(top_image, bottom_image)
            if not valid:
                raise HTTPException(status_code=400, detail=error_message)
                
            # STEP 2: Detection API calls to identify specific clothing items
            detection_tasks = [
                detect_clothing_items(client, top_content, "topwear"),
                detect_clothing_items(client, bottom_content, "bottomwear")
            ]
            try:
                top_detection_result, bottom_detection_result = await asyncio.gather(*detection_tasks)
                
                # Extract the highest confidence Shirt from topwear
                if top_detection_result and "detections" in top_detection_result:
                    shirt_detection = find_garment_by_class(
                        top_detection_result["detections"], 
                        "Shirt"
                    )
                    if shirt_detection:
                        logger.info(f"Found Shirt in topwear with confidence {shirt_detection.get('confidence', 0)}")
                        top_shirt_crop = extract_crop_from_detection(top_image, shirt_detection)
                    else:
                        logger.warning("No Shirt found in topwear image")
                
                # Extract the highest confidence Pants/Shorts from bottomwear
                if bottom_detection_result and "detections" in bottom_detection_result:
                    pants_detection = find_garment_by_class(
                        bottom_detection_result["detections"], 
                        "Pants/Shorts"
                    )
                    if pants_detection:
                        logger.info(f"Found Pants/Shorts in bottomwear with confidence {pants_detection.get('confidence', 0)}")
                        bottom_pants_crop = extract_crop_from_detection(bottom_image, pants_detection)
                    else:
                        logger.warning("No Pants/Shorts found in bottomwear image")
                
            except Exception as e:
                logger.warning(f"Detection API failed or no specific garments found, proceeding with full images: {str(e)}")
                # Continue without detection results
            
            # STEP 3: Feature extraction API calls
            # Use specific garment crops if available, otherwise use full images
            top_bytes = io.BytesIO()
            bottom_bytes = io.BytesIO()
            
            if top_shirt_crop:
                top_shirt_crop.save(top_bytes, format="JPEG")
                top_bytes.seek(0)
                logger.info("Using cropped Shirt image for feature extraction")
            else:
                top_image.save(top_bytes, format="JPEG")
                top_bytes.seek(0)
                logger.info("Using full topwear image for feature extraction")
                
            if bottom_pants_crop:
                bottom_pants_crop.save(bottom_bytes, format="JPEG")
                bottom_bytes.seek(0)
                logger.info("Using cropped Pants/Shorts image for feature extraction")
            else:
                bottom_image.save(bottom_bytes, format="JPEG")
                bottom_bytes.seek(0)
                logger.info("Using full bottomwear image for feature extraction")
            
            # Send to feature extraction API
            feature_tasks = [
                extract_features(client, top_bytes.getvalue(), "topwear"),
                extract_features(client, bottom_bytes.getvalue(), "bottomwear")
            ]
            top_feature_result, bottom_feature_result = await asyncio.gather(*feature_tasks)
        
        # STEP 4: Extract dominant colors for color harmony analysis
        # Use specific garment crops if available
        if top_shirt_crop:
            top_colors = extract_dominant_colors(top_shirt_crop)
        else:
            top_colors = extract_dominant_colors(top_image)
            
        if bottom_pants_crop:
            bottom_colors = extract_dominant_colors(bottom_pants_crop)
        else:
            bottom_colors = extract_dominant_colors(bottom_image)
        
        # STEP 5: Extract primary style from results (highest confidence)
        top_style = "casual"  # Default fallback
        bottom_style = "casual"  # Default fallback
        
        if top_style_result and "styles" in top_style_result and top_style_result["styles"]:
            # Sort by confidence and take the highest
            sorted_styles = sorted(top_style_result["styles"], key=lambda x: x["confidence"], reverse=True)
            top_style = sorted_styles[0]["style_name"].lower()
        
        if bottom_style_result and "styles" in bottom_style_result and bottom_style_result["styles"]:
            # Sort by confidence and take the highest
            sorted_styles = sorted(bottom_style_result["styles"], key=lambda x: x["confidence"], reverse=True)
            bottom_style = sorted_styles[0]["style_name"].lower()
        
        logger.info(f"Using top style: {top_style}, bottom style: {bottom_style}")
        
        # STEP 6: Get color families from dominant colors
        top_color_family = get_color_family(top_colors[0])
        bottom_color_family = get_color_family(bottom_colors[0])
        
        # STEP 7: Calculate match metrics
        
        # 7.1: Color harmony from dominant colors (K-means)
        color_score, color_analysis = calculate_color_harmony(top_colors, bottom_colors)
        
        # 7.2: Feature vector match
        feature_score = 0
        feature_analysis = "Feature analysis not available."
        if top_feature_result and bottom_feature_result:
            if "features" in top_feature_result and "features" in bottom_feature_result:
                feature_score, feature_analysis = calculate_feature_match_score(
                    top_feature_result["features"], 
                    bottom_feature_result["features"]
                )
        
        # 7.3: Color histogram match
        histogram_score = 0
        histogram_analysis = "Color histogram analysis not available."
        if top_feature_result and bottom_feature_result:
            if "color_histogram" in top_feature_result and "color_histogram" in bottom_feature_result:
                histogram_score, histogram_analysis = calculate_color_histogram_match(
                    top_feature_result["color_histogram"],
                    bottom_feature_result["color_histogram"]
                )
        
        # 7.4: Style consistency based on style classifications
        style_score, style_analysis = evaluate_style_consistency(top_style, bottom_style)
        
        # 7.5: Occasion appropriateness based on style and color
        occasion_score, occasion_analysis = analyze_occasion_appropriateness(
            top_style, bottom_style, top_color_family, bottom_color_family
        )
        
        # NOTE: Trend alignment has been removed
        
        # STEP 8: Calculate weighted overall match score with redistributed weights
        # New weights giving more importance to color/feature and less to style/occasion
        weights = {
            "color_harmony": 0.30,      # Dominant colors from K-means
            "feature_match": 0.25,      # Feature vectors (reduced from 0.30)
            "color_histogram": 0.20,    # Detailed color distribution (reduced from 0.25)
            "style_consistency": 0.20,  # Style classification (increased from 0.10)
            "occasion": 0.05,           # Occasion appropriateness
        }
        
        # If feature or histogram scores are not available, redistribute their weights
        if feature_score == 0:
            redistribution = weights["feature_match"] / 3  # Divide by 3 components
            weights["feature_match"] = 0
            weights["color_harmony"] += redistribution
            weights["style_consistency"] += redistribution
            weights["occasion"] += redistribution
            
        if histogram_score == 0:
            redistribution = weights["color_histogram"] / 3  # Divide by 3 components
            weights["color_histogram"] = 0
            weights["color_harmony"] += redistribution
            weights["style_consistency"] += redistribution
            weights["occasion"] += redistribution
        
        # Calculate weighted score
        weighted_score = (
            weights["color_harmony"] * color_score +
            weights["feature_match"] * feature_score +
            weights["color_histogram"] * histogram_score +
            weights["style_consistency"] * style_score +
            weights["occasion"] * occasion_score
        )
        
        # Apply a slight boost to make scores more generous
        # This adjusts the curve upward a bit, especially for mid-range scores
        boosted_score = min(100, weighted_score * 1.15)
        
        # Round to nearest integer
        overall_score = round(boosted_score)
        
        # STEP 9: Compile analysis results
        analysis = {
            "color_harmony": {
                "score": color_score,
                "analysis": color_analysis
            },
            "style_consistency": {
                "score": style_score,
                "analysis": style_analysis
            },
            "occasion_appropriateness": {
                "score": occasion_score,
                "analysis": occasion_analysis
            }
            # trend_alignment removed
        }
        
        # Add feature and histogram analysis if available
        if feature_score > 0:
            analysis["feature_match"] = {
                "score": feature_score,
                "analysis": feature_analysis
            }
            
        if histogram_score > 0:
            analysis["color_histogram_match"] = {
                "score": histogram_score,
                "analysis": histogram_analysis
            }
        
        # Generate suggestions
        suggestions = generate_suggestions(analysis)
        
        # Record match score metrics
        MATCH_SCORES.observe(overall_score)
        
        # Record color harmony scores
        if "color_harmony" in analysis:
            COLOR_HARMONY_SCORES.observe(analysis["color_harmony"]["score"])
        
        # Record style consistency scores
        if "style_consistency" in analysis:
            STYLE_CONSISTENCY_SCORES.observe(analysis["style_consistency"]["score"])
        
        # Measure processing time
        processing_time = time.time() - start_time
        MATCH_PROCESSING_TIME.observe(processing_time)
        
        return MatchResponse(
            match_score=overall_score,
            analysis=analysis,
            suggestions=suggestions,
            alternative_pairings=[]
        )
    except Exception as e:
        # Increment error counter
        MATCH_ERRORS.inc()
        
        logger.error(f"Error in match operation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing match request: {str(e)}")

@app.post("/compute_match", response_model=MatchResponse)
async def compute_match(request: MatchRequest):
    """
    Compute match based on preprocessed data.
    """
    # Increment the request counter
    MATCH_REQUESTS.inc()
    
    start_time = time.time()
    try:
        logger.info("Processing match from preprocessed data")
        
        # Extract data from request
        top_style = request.top_style
        bottom_style = request.bottom_style
        top_vector = request.top_vector
        bottom_vector = request.bottom_vector
        top_histogram = request.top_histogram
        bottom_histogram = request.bottom_histogram
        
        # Set default dominant colors in case we can't extract from the histogram
        top_colors = [(0.2, 0.3, 0.8), (0.1, 0.1, 0.1)]  # Default blue and black
        bottom_colors = [(0.8, 0.8, 0.8), (0.1, 0.1, 0.1)]  # Default white and black
        
        # Try to extract dominant colors from color histograms if available
        if top_histogram and len(top_histogram) > 0:
            try:
                # The histogram is now organized as [R bins..., G bins..., B bins...]
                # Each channel has bins_per_channel bins (usually 8)
                hist_length = len(top_histogram)
                bins_per_channel = hist_length // 3
                
                # Get the R, G, B histograms
                r_hist = top_histogram[:bins_per_channel]
                g_hist = top_histogram[bins_per_channel:2*bins_per_channel]
                b_hist = top_histogram[2*bins_per_channel:]
                
                # Find the peak bin for each channel
                r_peak_bin = r_hist.index(max(r_hist))
                g_peak_bin = g_hist.index(max(g_hist))
                b_peak_bin = b_hist.index(max(b_hist))
                
                # Convert bin indices to color values (0-255)
                bin_width = 256 / bins_per_channel
                r_peak = int((r_peak_bin + 0.5) * bin_width)
                g_peak = int((g_peak_bin + 0.5) * bin_width)
                b_peak = int((b_peak_bin + 0.5) * bin_width)
                
                # Set as the dominant color (in 0-1 range)
                top_colors[0] = (r_peak / 255, g_peak / 255, b_peak / 255)
                logger.info(f"Extracted top dominant color: RGB({r_peak}, {g_peak}, {b_peak})")
            except Exception as e:
                logger.error(f"Error extracting dominant colors from top histogram: {e}")
                # Keep using default colors if extraction fails
        
        if bottom_histogram and len(bottom_histogram) > 0:
            try:
                # Same process for bottom
                hist_length = len(bottom_histogram)
                bins_per_channel = hist_length // 3
                
                # Get the R, G, B histograms
                r_hist = bottom_histogram[:bins_per_channel]
                g_hist = bottom_histogram[bins_per_channel:2*bins_per_channel]
                b_hist = bottom_histogram[2*bins_per_channel:]
                
                # Find the peak bin for each channel
                r_peak_bin = r_hist.index(max(r_hist))
                g_peak_bin = g_hist.index(max(g_hist))
                b_peak_bin = b_hist.index(max(b_hist))
                
                # Convert bin indices to color values (0-255)
                bin_width = 256 / bins_per_channel
                r_peak = int((r_peak_bin + 0.5) * bin_width)
                g_peak = int((g_peak_bin + 0.5) * bin_width)
                b_peak = int((b_peak_bin + 0.5) * bin_width)
                
                # Set as the dominant color (in 0-1 range)
                bottom_colors[0] = (r_peak / 255, g_peak / 255, b_peak / 255)
                logger.info(f"Extracted bottom dominant color: RGB({r_peak}, {g_peak}, {b_peak})")
            except Exception as e:
                logger.error(f"Error extracting dominant colors from bottom histogram: {e}")
                # Keep using default colors if extraction fails
        
        # If we have actual detections, try to extract more information
        if request.top_detection:
            # In a real implementation, this might use the detection crop for more analysis
            logger.info(f"Using top detection: {request.top_detection.get('class_name', 'unknown')}")
            
        if request.bottom_detection:
            logger.info(f"Using bottom detection: {request.bottom_detection.get('class_name', 'unknown')}")
            
        # Get color families (simplified)
        top_color_family = get_color_family(top_colors[0])
        bottom_color_family = get_color_family(bottom_colors[0])
        
        logger.info(f"Color families: top={top_color_family}, bottom={bottom_color_family}")
        
        # STEP 1: Calculate match metrics
        
        # 1.1: Color harmony from dominant colors
        color_score, color_analysis = calculate_color_harmony(top_colors, bottom_colors)
        
        # 1.2: Feature vector match
        feature_score = 0
        feature_analysis = "Feature analysis not available."
        if top_vector and bottom_vector:
            feature_score, feature_analysis = calculate_feature_match_score(top_vector, bottom_vector)
        
        # 1.3: Color histogram match
        histogram_score = 0
        histogram_analysis = "Color histogram analysis not available."
        if top_histogram and bottom_histogram:
            histogram_score, histogram_analysis = calculate_color_histogram_match(top_histogram, bottom_histogram)
        
        # 1.4: Style consistency based on style classifications
        style_score, style_analysis = evaluate_style_consistency(top_style, bottom_style)
        
        # 1.5: Occasion appropriateness based on style and color
        occasion_score, occasion_analysis = analyze_occasion_appropriateness(
            top_style, bottom_style, top_color_family, bottom_color_family
        )
        
        # STEP 2: Calculate weighted overall match score
        weights = {
            "color_harmony": 0.30,      # Dominant colors from K-means
            "feature_match": 0.25,      # Feature vectors (reduced from 0.30)
            "color_histogram": 0.20,    # Detailed color distribution (reduced from 0.25)
            "style_consistency": 0.20,  # Style classification (increased from 0.10)
            "occasion": 0.05,           # Occasion appropriateness
        }
        
        # If feature or histogram scores are not available, redistribute their weights
        if feature_score == 0:
            redistribution = weights["feature_match"] / 3  # Divide by 3 components
            weights["feature_match"] = 0
            weights["color_harmony"] += redistribution
            weights["style_consistency"] += redistribution
            weights["occasion"] += redistribution
            
        if histogram_score == 0:
            redistribution = weights["color_histogram"] / 3  # Divide by 3 components
            weights["color_histogram"] = 0
            weights["color_harmony"] += redistribution
            weights["style_consistency"] += redistribution
            weights["occasion"] += redistribution
        
        # Calculate weighted score
        weighted_score = (
            weights["color_harmony"] * color_score +
            weights["feature_match"] * feature_score +
            weights["color_histogram"] * histogram_score +
            weights["style_consistency"] * style_score +
            weights["occasion"] * occasion_score
        )
        
        # Apply a slight boost to make scores more generous
        # This adjusts the curve upward a bit, especially for mid-range scores
        boosted_score = min(100, weighted_score * 1.15)
        
        # Round to nearest integer
        overall_score = round(boosted_score)
        
        # STEP 3: Compile analysis results
        analysis = {
            "color_harmony": {
                "score": color_score,
                "analysis": color_analysis
            },
            "style_consistency": {
                "score": style_score,
                "analysis": style_analysis
            },
            "occasion_appropriateness": {
                "score": occasion_score,
                "analysis": occasion_analysis
            }
        }
        
        # Add feature and histogram analysis if available
        if feature_score > 0:
            analysis["feature_match"] = {
                "score": feature_score,
                "analysis": feature_analysis
            }
            
        if histogram_score > 0:
            analysis["color_histogram_match"] = {
                "score": histogram_score,
                "analysis": histogram_analysis
            }
        
        # Generate suggestions
        suggestions = generate_suggestions(analysis)
        
        # Record match score metrics
        MATCH_SCORES.observe(overall_score)
        
        # Record color harmony scores if available
        if "color_harmony" in analysis:
            COLOR_HARMONY_SCORES.observe(analysis["color_harmony"]["score"])
        
        # Record style consistency scores if available
        if "style_consistency" in analysis:
            STYLE_CONSISTENCY_SCORES.observe(analysis["style_consistency"]["score"])
        
        # Measure processing time
        processing_time = time.time() - start_time
        MATCH_PROCESSING_TIME.observe(processing_time)
        
        return MatchResponse(
            match_score=overall_score,
            analysis=analysis,
            suggestions=suggestions,
            alternative_pairings=None
        )
    except Exception as e:
        # Increment error counter
        MATCH_ERRORS.inc()
        
        logger.error(f"Error in compute_match operation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing match request: {str(e)}")

# Run the app if executed directly
if __name__ == "__main__":
    uvicorn.run("match_api:app", host="0.0.0.0", port=8008, reload=True) 
from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Body, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
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
    
    # Convert RGB to HSV
    h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
    
    # Convert hue to degrees (0-360)
    h_degrees = h * 360
    
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
    if is_top_neutral or is_bottom_neutral:
        harmony_score = 0.6 * neutral_score + 0.4 * brightness_score
    else:
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
            "formal": 30,
            "sports": 70,
            "ethnic": 60,
            "business": 40,
            "party": 60
        },
        "formal": {
            "casual": 30,
            "formal": 95,
            "sports": 10,
            "ethnic": 50,
            "business": 85,
            "party": 70
        },
        "sports": {
            "casual": 70,
            "formal": 10,
            "sports": 95,
            "ethnic": 20,
            "business": 15,
            "party": 30
        },
        "ethnic": {
            "casual": 60,
            "formal": 50,
            "sports": 20,
            "ethnic": 95,
            "business": 45,
            "party": 75
        },
        "business": {
            "casual": 40,
            "formal": 85,
            "sports": 15,
            "ethnic": 45,
            "business": 95,
            "party": 60
        },
        "party": {
            "casual": 60,
            "formal": 70,
            "sports": 30,
            "ethnic": 75,
            "business": 60,
            "party": 95
        }
    }
    
    # Default score for unknown styles
    default_score = 50
    
    # Get compatibility score
    score = compatibility_matrix.get(top_style, {}).get(bottom_style, default_score)
    
    # Generate analysis text
    if score >= 85:
        analysis = f"Excellent {top_style}-{bottom_style} style matching."
    elif score >= 70:
        analysis = f"Good style consistency between {top_style} top and {bottom_style} bottom."
    elif score >= 50:
        analysis = f"{top_style.capitalize()} top and {bottom_style} bottom are compatible with careful styling."
    else:
        analysis = f"{top_style.capitalize()} top and {bottom_style} bottom have contrasting styles that may clash."
    
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
    
    # Suggestions based on specific scores
    if color_score < 70:
        suggestions.append("Consider items with more complementary or harmonious colors.")
    
    if style_score < 70:
        suggestions.append("Try pieces that are more consistent in style or formality level.")
    
    # Generic suggestions that enhance most outfits
    styling_suggestions = [
        "Adding a belt would help tie this look together.",
        "Accessories like a watch or jewelry could elevate this combination.",
        "Footwear in a neutral tone would complement this outfit well.",
        "Consider layering with a jacket or cardigan for added dimension."
    ]
    
    # Add 1-2 generic styling suggestions
    import random
    random.shuffle(styling_suggestions)
    suggestions.extend(styling_suggestions[:2])
    
    return suggestions[:3]  # Limit to 3 suggestions

async def validate_clothing_types(top_image, bottom_image):
    """Validate that images are indeed top and bottom wear"""
    # This would normally use the style_iep to validate clothing types
    # For this prototype, we'll return a simplified validation
    # In production, this should make actual API calls to style_iep
    
    # Simulate validation with random success rate for demo
    # In production, replace with actual service calls
    validation_success = True  # Assume valid for now
    
    if validation_success:
        return True, None
    else:
        return False, "Unable to confirm clothing types. Please ensure one image is topwear and one is bottomwear."

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

@app.post("/match", response_model=MatchResponse)
async def match_outfit(
    topwear: UploadFile = File(...),
    bottomwear: UploadFile = File(...)
):
    """
    Calculate match score and analysis between topwear and bottomwear items
    """
    try:
        # Process uploaded images
        top_content = await topwear.read()
        bottom_content = await bottomwear.read()
        
        # Convert to PIL images
        top_image = Image.open(io.BytesIO(top_content)).convert('RGB')
        bottom_image = Image.open(io.BytesIO(bottom_content)).convert('RGB')
        
        # Validate clothing types (would call style_iep in production)
        valid, error_message = await validate_clothing_types(top_image, bottom_image)
        if not valid:
            raise HTTPException(status_code=400, detail=error_message)
        
        # Extract dominant colors
        top_colors = extract_dominant_colors(top_image)
        bottom_colors = extract_dominant_colors(bottom_image)
        
        # For demo purposes, assign styles
        # In production, these would come from style_iep
        top_style = "casual"  # Placeholder
        bottom_style = "casual"  # Placeholder
        
        # Get color families
        top_color_family = get_color_family(top_colors[0])
        bottom_color_family = get_color_family(bottom_colors[0])
        
        # Calculate match metrics
        color_score, color_analysis = calculate_color_harmony(top_colors, bottom_colors)
        style_score, style_analysis = evaluate_style_consistency(top_style, bottom_style)
        occasion_score, occasion_analysis = analyze_occasion_appropriateness(
            top_style, bottom_style, top_color_family, bottom_color_family
        )
        trend_score, trend_analysis = calculate_trend_alignment(top_style, bottom_style)
        
        # Calculate weighted overall match score
        overall_score = round(
            0.4 * color_score +
            0.3 * style_score +
            0.2 * occasion_score +
            0.1 * trend_score
        )
        
        # Compile analysis results
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
            },
            "trend_alignment": {
                "score": trend_score,
                "analysis": trend_analysis
            }
        }
        
        # Generate suggestions
        suggestions = generate_suggestions(analysis)
        
        # For demo, no alternative pairings yet
        # In production, these would come from reco_data_iep
        alternative_pairings = []
        
        # Prepare response
        response = {
            "match_score": overall_score,
            "analysis": analysis,
            "suggestions": suggestions,
            "alternative_pairings": alternative_pairings
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing match request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing match request: {str(e)}")

# Run the app if executed directly
if __name__ == "__main__":
    uvicorn.run("match_api:app", host="0.0.0.0", port=8008, reload=True) 
# Matching Internal Endpoint Processor (IEP)

This service evaluates the matchability of clothing items, specifically determining how well a topwear item pairs with a bottomwear item.

## Overview

The Matching IEP analyzes clothing pairs across multiple dimensions:
- Color harmony
- Feature vector similarity
- Color histogram matching
- Style consistency
- Occasion appropriateness
- Trend alignment

It provides a comprehensive match score along with detailed analysis and styling suggestions.

## Features

- **Topwear/Bottomwear Validation**: Ensures the provided items are correctly identified using the Style IEP
- **Specific Garment Detection**: Uses Detection IEP to isolate specific clothing items (Shirt for topwear, Pants/Shorts for bottomwear)
- **Color Analysis**: Evaluates color compatibility using color theory principles
- **Feature Vector Matching**: Uses cosine similarity to compare deep learning feature embeddings from Feature IEP
- **Advanced Color Histogram Matching**: Evaluates color distribution compatibility using both similarity and contrast metrics
- **Style Compatibility**: Assesses style consistency between different clothing types using real style classifications from the Style IEP
- **Occasion Matching**: Determines appropriate settings for the outfit
- **Fashion Trend Alignment**: Evaluates how trendy the combination is
- **Styling Suggestions**: Provides actionable recommendations for improvement

## Matching Algorithm

### Detection and Processing Pipeline

1. **Clothing Detection**:
   - Uses Detection IEP to identify specific garments in the uploaded images
   - Locates "Shirt" in topwear image and "Pants/Shorts" in bottomwear image
   - Extracts cropped regions of the detected clothing items for more accurate analysis

2. **Feature Extraction**:
   - Sends detected garment crops to Feature IEP 
   - Extracts feature vectors and color histograms from the specific garments
   - Falls back to full image if specific garments aren't detected

### Scoring Components

The overall match score is a weighted combination of:

| Component | Weight | Justification |
|-----------|--------|---------------|
| Color Harmony | 20% | Visual perception of dominant colors is immediately noticeable |
| Feature Match | 20% | Deep learning embeddings capture learned patterns of compatibility |
| Color Histogram | 15% | Detailed color distribution provides nuanced color compatibility |
| Style Consistency | 20% | Explicit style categorization ensures appropriate pairings |
| Occasion Appropriateness | 15% | Situational context is important for outfit utility |
| Trend Alignment | 10% | Fashion relevance affects perception but is less critical |

If any component is unavailable (e.g., feature extraction fails), its weight is redistributed proportionally among other components.

### Vector Similarity Metrics

- **Cosine Similarity**: Used for feature vectors as it focuses on the direction/pattern rather than magnitude, which is ideal for high-dimensional embeddings that capture semantic relationships

- **Enhanced Color Histogram Matching**: 
  - Uses a U-shaped scoring function that rewards both similar colors (monochromatic schemes) and complementary colors (high contrast)
  - Calculates color entropy to measure color diversity and contrast
  - Combines similarity measures with entropy difference for a comprehensive color compatibility score
  - Recognizes that both very similar and very different color distributions can work well in fashion

## API Endpoints

The service exposes the following endpoints:

- `GET /`: Root endpoint with information about the service
- `GET /health`: Health check endpoint
- `POST /match`: Evaluate matchability between topwear and bottomwear items

## Usage

### POST /match

**Request:**
```
POST /match
```

Form data:
- `topwear`: Image file of top clothing item
- `bottomwear`: Image file of bottom clothing item

**Response:**
```json
{
  "match_score": 85,
  "analysis": {
    "color_harmony": {
      "score": 90,
      "analysis": "Good complementary color pairing between navy top and khaki bottom."
    },
    "feature_match": {
      "score": 88,
      "analysis": "Excellent feature compatibility indicating harmonious outfit composition."
    },
    "color_histogram_match": {
      "score": 82,
      "analysis": "Bold contrasting color combination creating visual interest."
    },
    "style_consistency": {
      "score": 80,
      "analysis": "Both items fall within business casual category."
    },
    "occasion_appropriateness": {
      "score": 85,
      "analysis": "Suitable for office environment or casual business meetings."
    },
    "trend_alignment": {
      "score": 75,
      "analysis": "Classic combination with contemporary elements."
    }
  },
  "suggestions": [
    "Consider adding a brown leather belt to complete the look.",
    "A silver watch would complement this outfit well."
  ]
}
```

## Integration with Services

This service integrates with multiple IEPs:

1. **Style IEP**: Gets actual style classifications for both items
2. **Detection IEP**: Identifies specific clothing items in images for targeted analysis
3. **Feature IEP**: Extracts feature vectors and color histograms for advanced matching

## Configuration

Configure the service through environment variables:
- `FEATURE_SERVICE_URL`: URL to Feature IEP (default: http://feature-iep:8003)
- `STYLE_SERVICE_URL`: URL to Style IEP (default: http://style-iep:8002)
- `SERVICE_TIMEOUT`: Timeout for internal service requests in seconds (default: 30)

## Development

### Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run the service
uvicorn match_api:app --reload --host 0.0.0.0 --port 8008
```

### Docker

```bash
# Build the image
docker build -t match-iep .

# Run the container
docker run -p 8008:8008 match-iep
```

## Integration with EEP

This service is designed to be called by the External Endpoint Processor (EEP) which handles user interfaces and coordinates between services.

## Future Enhancements

- Integration with recommendation system for alternative pairings
- User preference learning for personalized matching
- Season-appropriate outfit analysis
- Integration with virtual try-on to visualize matches 
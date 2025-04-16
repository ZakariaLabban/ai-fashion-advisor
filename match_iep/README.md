# Matching Internal Endpoint Processor (IEP)

This service evaluates the matchability of clothing items, specifically determining how well a topwear item pairs with a bottomwear item.

## Overview

The Matching IEP analyzes clothing pairs across multiple dimensions:
- Color harmony (K-means clustering)
- Feature vector similarity
- Color histogram matching
- Style consistency
- Occasion appropriateness

It provides a comprehensive match score along with detailed analysis and styling suggestions.

## Features

- **Score-only Processing**: Focuses solely on calculating match scores based on pre-processed data received from the External Endpoint Processor (EEP)
- **Dominant Color Analysis (K-means)**: Evaluates color compatibility using color theory principles
- **Feature Vector Matching**: Uses cosine similarity to compare deep learning feature embeddings
- **Advanced Color Histogram Matching**: Evaluates color distribution compatibility using both similarity and contrast metrics
- **Style Compatibility**: Assesses style consistency between different clothing types
- **Occasion Matching**: Determines appropriate settings for the outfit
- **Styling Suggestions**: Provides actionable recommendations for improvement

## Matching Algorithm

### Scoring Components

The overall match score is a weighted combination of:

| Component | Weight | Justification |
|-----------|--------|---------------|
| Color Harmony (K-means) | 30% | Visual perception of dominant colors is immediately noticeable |
| Feature Match | 30% | Deep learning embeddings capture learned patterns of compatibility |
| Color Histogram | 25% | Detailed color distribution provides nuanced color compatibility |
| Style Consistency | 10% | Style categorization ensures appropriate pairings |
| Occasion Appropriateness | 5% | Situational context provides additional context |

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
- `POST /match`: Legacy endpoint for direct image submission (for backwards compatibility)
- `POST /compute_match`: **New** Accepts pre-processed data for scoring only

## Updated Architecture

This service has been refactored to follow a centralized data processing pattern:

1. The External Endpoint Processor (EEP) handles all inter-service communication:
   - EEP sends images to Detection IEP
   - EEP sends images to Style IEP
   - EEP sends detected garment crops to Feature IEP
   - EEP consolidates all results from these services

2. The Match IEP now focuses solely on its core competency:
   - Receiving pre-processed data (styles, features, histograms) from the EEP
   - Computing match scores and generating analysis
   - Providing styling recommendations

This architecture has the following benefits:
- Reduced network traffic between services
- Decreased latency by parallelizing requests
- Improved fault isolation
- Simplified service responsibilities

## Usage

### POST /compute_match (New Endpoint)

**Request:**
```json
{
  "top_style": "casual",
  "bottom_style": "casual",
  "top_vector": [0.2, 0.5, 0.1, ...],
  "bottom_vector": [0.3, 0.4, 0.2, ...],
  "top_histogram": [0.1, 0.2, 0.3, ...],
  "bottom_histogram": [0.2, 0.1, 0.3, ...],
  "top_detection": {
    "class_name": "Shirt",
    "confidence": 0.95,
    "bbox": [10, 20, 100, 200]
  },
  "bottom_detection": {
    "class_name": "Pants",
    "confidence": 0.92,
    "bbox": [15, 250, 110, 450]
  }
}
```

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
    }
  },
  "suggestions": [
    "Consider adding a brown leather belt to complete the look.",
    "A silver watch would complement this outfit well."
  ]
}
```

### POST /match (Legacy Endpoint)

This endpoint is maintained for backward compatibility. It still accepts direct image uploads but internally the EEP now handles all the communication with other services.

## Configuration

Configure the service through environment variables:
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

This service now follows a centralized processing model where the External Endpoint Processor (EEP) coordinates all data flow between services and the Match IEP focuses solely on calculating match scores and analysis. 
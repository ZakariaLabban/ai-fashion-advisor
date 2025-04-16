# Matching Internal Endpoint Processor (IEP)

This service evaluates the matchability of clothing items, specifically determining how well a topwear item pairs with a bottomwear item.

## Overview

The Matching IEP analyzes clothing pairs across multiple dimensions:
- Color harmony
- Style consistency
- Occasion appropriateness
- Trend alignment

It provides a comprehensive match score along with detailed analysis and styling suggestions.

## Features

- **Topwear/Bottomwear Validation**: Ensures the provided items are correctly identified using the Style IEP
- **Color Analysis**: Evaluates color compatibility using color theory principles
- **Style Compatibility**: Assesses style consistency between different clothing types using real style classifications from the Style IEP
- **Occasion Matching**: Determines appropriate settings for the outfit
- **Fashion Trend Alignment**: Evaluates how trendy the combination is
- **Styling Suggestions**: Provides actionable recommendations for improvement

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

## Integration with Style IEP

This service now integrates with the Style IEP to get actual style classifications rather than using hardcoded placeholder values:

1. When images are uploaded, they are first validated through the Style IEP
2. The Style IEP performs style classification on both topwear and bottomwear images
3. The highest confidence style for each item is used for the matching analysis
4. The style information feeds into style consistency, occasion appropriateness, and trend alignment analysis

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
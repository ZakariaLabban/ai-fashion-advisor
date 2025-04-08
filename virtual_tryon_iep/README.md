# Virtual Try-On Internal Endpoint Processor (IEP)

This directory contains the Virtual Try-On IEP service that is integrated with the Fashion Analysis EEP system.

## Overview

The Virtual Try-On IEP provides endpoints for:
- Single garment try-on: Allows trying on a single garment on a model image
- Multi-garment try-on: Allows trying on both top and bottom garments on a model image

## API Endpoints

The service exposes the following endpoints:

- `GET /`: Root endpoint with information about the service
- `GET /health`: Health check endpoint
- `POST /tryon`: Process a single garment try-on
- `POST /tryon/multi`: Process a multi-garment try-on

## Integration with EEP

This IEP is integrated with the main EEP and provides virtual try-on capabilities to the overall system. The EEP communicates with this service using base64 encoded images and handles all user interactions.

## Placeholder Images

The service includes placeholder images in the `static/placeholders` directory:
- Model images: Example person images suitable for try-on
- Garment images: Example clothing items to try on
- Result images: Example output of the try-on process

These placeholders serve as examples and can be used for testing the service.

## Configuration

All configuration is done through environment variables in the docker-compose.yml file or a local .env file:

```
FASHN_AI_API_KEY=your_api_key_here
FASHN_AI_BASE_URL=https://api.fashn.ai/v1
``` 
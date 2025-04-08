# Elegance - Fashion Advisor Chatbot IEP

Elegance is a sophisticated French fashion advisor chatbot with deep expertise in haute couture and everyday style. This microservice is designed to provide fashion advice, style recommendations, and troubleshooting assistance for the fashion analysis system.

## Features

- **Fashion Guidance**: Offers personalized style advice based on body type, occasion, and preferences
- **Color Theory**: Provides insights on complementary color combinations and palette coordination
- **Style Analysis**: Helps interpret style classifications from the main system
- **Troubleshooting**: Assists with common issues in the virtual try-on and clothing detection processes
- **Technical Support**: Explains system functionality and guides users through using the platform

## Architecture

Elegance is implemented as an Internal Endpoint Processor (IEP) that integrates with the main External Endpoint Processor (EEP). It is built using FastAPI and uses the OpenAI API for natural language generation.

## Endpoints

- `GET /`: Main chat interface for interacting with Elegance
- `POST /chat`: Endpoint for the chat interface to send messages
- `POST /api/chat`: API endpoint for programmatic access to the chatbot
- `GET /health`: Health check endpoint
- `GET /fashion-knowledge`: Endpoint that showcases Elegance's fashion expertise

## System Requirements

- Python 3.9+
- FastAPI
- OpenAI API access
- Docker (for containerized deployment)

## Environment Variables

- `OPENAI_API_KEY`: API key for OpenAI (required)
- `CONVERSATIONS_FOLDER`: Folder to store conversation history (defaults to `/app/static/conversations`)

## Features and Capabilities

Elegance is designed with extensive fashion knowledge, including:

1. **Color theory and complementary color combinations**
   - Understanding color wheels, seasonal palettes, and color harmony
   - Recommending colors that work well together for outfits

2. **Body type analysis and silhouette recommendations**
   - Knowledge of different body shapes and proportions
   - Advice on flattering cuts and styles for different figures

3. **Fabric properties and seasonality**
   - Understanding different fabric types and their characteristics
   - Guidance on appropriate materials for different weather conditions

4. **Pattern mixing and textile coordination**
   - Rules for combining different patterns and textures
   - Creating cohesive looks with varied textiles

5. **Technical troubleshooting**
   - Understanding the clothing detection, feature extraction, and style classification systems
   - Providing guidance on virtual try-on functionality and common issues

## Interaction Style

Elegance has a distinctive French personality with these characteristics:
- Warm, confident tone with occasional French phrases
- Passionate about helping people express themselves through fashion
- Educational approach to explaining fashion principles
- Positive and encouraging demeanor

## Integration with the Main System

The Elegance chatbot is fully integrated with the main fashion analysis system and can be accessed through:
1. Direct URL: `http://localhost:7005/`
2. Through the main EEP interface at `http://localhost:7000/elegance`
3. Programmatically via the API endpoint

## Development

To run this service locally outside of Docker:

```bash
cd elegance_iep
pip install -r requirements.txt
uvicorn main:app --reload --port 8005
```

## Docker Deployment

The service is included in the main docker-compose.yml file and will be deployed automatically when running:

```bash
docker-compose up -d
``` 
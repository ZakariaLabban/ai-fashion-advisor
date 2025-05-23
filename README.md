# AI Fashion Advisor
A comprehensive system that combines computer vision and artificial intelligence to provide fashion analysis, virtual try-on, personalized style advice, and clothing recommendations.

## Overview

AI Fashion Advisor leverages advanced deep learning models to detect clothing items, extract features, classify styles, and offer virtual try-on capabilities. The platform integrates recommendation systems and AI-powered fashion advice to create a complete fashion technology solution.

## Features

- **Clothing Detection**: Identify and segment clothing items in images
- **Style Classification**: Automatically categorize clothing by style and type
- **Virtual Try-On**: See how garments look on models without physical fitting
- **AI Fashion Assistant**: Get personalized style advice from an AI chatbot
- **Recommendation System**: Find matching or similar clothing items based on color and style
- **Modern React Frontend**: Sleek, responsive UI built with React and Tailwind CSS
- **Outfit Matching**: Evaluate how well tops and bottoms match and get styling suggestions
- **Text-to-Image Search**: Find clothing items by natural language description
- **Person Detection**: Identify and locate people in images for better processing

## Architecture

The system is built using a microservices architecture with the following components:

1. **React Frontend (AURAI)**: Modern, responsive UI built with React and Tailwind CSS
   - Clean, modern design with Tailwind CSS
   - Mobile-friendly interface
   - Built with Vite for optimized development and production builds

2. **External Endpoint Processor (EEP)**: Main entry point that coordinates all services
   - Handles inter-service communication
   - Routes requests to appropriate services
   - Consolidates results from multiple services

3. **Detection IEP**: Detects clothing items in images using YOLOv8
   - Identifies and segments clothing items
   - Provides bounding box coordinates

4. **Feature IEP**: Extracts feature vectors from clothing items with ResNet50
   - Generates feature embeddings for similarity searches
   - Creates color histograms for color matching

5. **Style IEP**: Classifies clothing styles using a fine-tuned YOLOv8 model
   - Categorizes clothing by style (casual, formal, etc.)
   - Identifies the type of clothing item

6. **Virtual Try-On IEP**: Enables virtual clothing try-on via FASHN.AI API
   - Supports trying on tops and bottoms
   - Requires model image and garment image
   - Provides clear guidelines for optimal results

7. **Elegance IEP**: AI fashion advisor chatbot built with OpenAI
   - Offers fashion advice and styling tips
   - Helps users navigate the system

8. **Recommendation Data IEP**: Provides clothing recommendations and similarity search
   - Uses Qdrant for vector similarity search
   - Uses MySQL for metadata storage and filtering
   - Uses Google Drive for image storage and retrieval
   - Offers matching recommendations (e.g., bottom to match a top)
   - Provides similarity search (e.g., similar shirts)

9. **Match IEP**: Evaluates compatibility between top and bottom garments
   - Analyzes clothing pairs across multiple dimensions:
     - Color harmony (K-means clustering)
     - Feature vector similarity
     - Color histogram matching
     - Style consistency
     - Occasion appropriateness
   - Provides comprehensive match scores and detailed analysis
   - Offers styling suggestions for improvement

10. **Text-to-Image IEP**: Enables natural language search for clothing items
    - Converts text descriptions to CLIP embeddings for semantic search
    - Filters queries to ensure they're clothing-related using GPT-4o-mini
    - Searches the Qdrant vector database for matching clothing items
    - Retrieves images from Google Drive based on search results
    - Provides monitoring and metrics for performance tracking

11. **Person Detector IEP**: Specialized service for detecting people in images
    - Uses YOLOv8 model optimized for person detection
    - Identifies and provides bounding boxes for people in images
    - Can optionally return cropped images of detected persons
    - Supports confidence threshold adjustment for detection sensitivity
    - Includes Prometheus metrics for monitoring service performance

## Model Files

This project uses several large model files that are not included in the repository:

- `yolov8_clothing_detection_segmentation.pt` - YOLOv8 fine-tuned model on DeepFashion dataset for detecting and segmenting clothes
- `yolov8_style_model.pt` - YOLOv8 fined-tuned model for style classification
- `multitask_resnet50_finetuned.pt` - Fine-tuned ResNet50 for feature extraction
- `yolov8n.pt` - Pre-trained model on COCO dataset for people detection.

## Prerequisites

- Docker and Docker Compose
- FASHN.AI API key (for virtual try-on)
- OpenAI API key (for fashion advice chatbot)
- MySQL database (for recommendation data)
- Qdrant vector database (for vector similarity search)
- Google Drive API credentials (for image storage)

## Getting Started

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/yourusername/ai-fashion-advisor.git
   cd ai-fashion-advisor
   ```

2. **Obtain model files**

   Download the required model files and place them in the project root:
   - `yolov8_clothing_detection_segmentation.pt`
   - `yolov8_style_model.pt`
   - `multitask_resnet50_finetuned.pt`
   - `yolov8n.pt`


3. **Create environment file**

   Create a single `.env` file in the root directory with all required environment variables:

   ```
   # AI API Keys
   FASHN_AI_API_KEY=your-fashn-api-key
   FASHN_AI_BASE_URL=https://api.fashn.ai/v1
   OPENAI_API_KEY=your-openai-api-key

   # Database Configuration
   MYSQL_HOST=your-mysql-host
   MYSQL_PORT=3306
   MYSQL_USER=username
   MYSQL_PASSWORD=password
   MYSQL_DATABASE=your_database

   # Vector Database Configuration
   QDRANT_URL=https://your-qdrant-cloud-url
   QDRANT_API_KEY=your-qdrant-api-key
   COLLECTION_NAME=fashion_features

   # Google Drive Configuration
   SEGMENTED_FOLDER_ID=your_google_drive_folder_id_for_segmented
   FULL_FOLDER_ID=your_google_drive_folder_id_for_full_images
   SERVICE_ACCOUNT_FILE= your_service_account.json
   ```

   ### Migration from Multiple .env Files

   If you're migrating from a previous version that used multiple .env files, follow these steps:

   1. Create a new `.env` file in the project root directory
   2. Copy all environment variables from these files to the new file:
      - `.env` (root directory)
      - `reco_data_iep/.env`
      - `text2image_iep/.env`
      - `virtual_tryon_iep/.env`
   3. Remove duplicate entries if the same variable is defined in multiple files
   4. You can safely delete the old .env files after migration

4. **Obtain Google Drive API credentials**

   - Create a service account in Google Cloud Console
   - Download the JSON credentials file and rename it to `auradataset-a28919b443a7.json`
   - Place it in the `reco_data_iep` directory
   - Share your Google Drive folders with the service account email

5. **Obtain MySQL SSL certificate**

   - Download your MySQL SSL certificate
   - Rename it to `ca.pem` and place it in the `reco_data_iep` directory

6. **Build and run with Docker**

   ```bash
   docker-compose up -d
   ```

7. **Access the application**

   - Modern React Frontend: [http://localhost:3000](http://localhost:3000)
   - Original Web Interface: [http://localhost:7000](http://localhost:7000)

## Usage Guide

### Analyzing Clothing

1. Navigate to "Analyze Your Fit"
2. Upload an image containing clothing items
3. View detected items with style classifications and feature information

### Virtual Try-On

1. Go to the "Fitting Room" section
2. Upload a model image (person)
3. Upload a garment image (clothing item)
4. Click "Try On Garment" to see the results

#### Guidelines for Good Virtual Try-On Results:

##### Model Images
- Use full-body photos with the person standing in a neutral pose
- Use a solid, contrasting background for best results
- The person should wear simple, solid-colored clothing
- Resolution should be at least 512x768 pixels

##### Garment Images
- Use product-style images with the garment against a white/transparent background
- The garment should be centered and take up most of the frame
- For tops: show the entire garment from collar to hem
- For bottoms: show the entire garment from waist to hem
- Resolution should be at least 512x512 pixels

### Outfit Matching

1. Go to the "Outfit Matcher" section
2. Upload a top garment image
3. Upload a bottom garment image
4. Click "Check Match" to see how well they go together
5. Review the match score and detailed analysis
6. Get styling suggestions for improvement

The matching algorithm evaluates:
- Color harmony using K-means clustering
- Feature vector similarity
- Color histogram matching
- Style consistency
- Occasion appropriateness

### Fashion Advice

1. Visit the "Elegance Bot" section
2. Chat with the AI advisor for style guidance
3. Ask questions about fashion rules, outfit combinations, or get help with using the system

### Finding Matching or Similar Items

1. Go to the "Recommender" section
2. Upload a clothing item
3. Choose whether to find a matching item (e.g., bottom to match a top) or similar items
4. View the recommended items

### Text-to-Image Search
1. Navigate to the Fashion Finder" section
2. Type a descriptive query about the clothing you're looking for (e.g., "blue denim jacket" or "floral summer dress")
3. Click "Enter" to find clothing items matching your description


## API Reference

### Main Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/analyze` | POST | Analyze clothing in uploaded image |
| `/tryon` | POST | Virtual try-on with a model and garment |
| `/tryon/multi` | POST | Try multiple garments (top and bottom) |
| `/elegance` | GET | Access the fashion advisor chatbot |
| `/api/elegance/chat` | POST | Chat API for the fashion advisor |
| `/recommendation/matching` | POST | Find matching clothing items |
| `/recommendation/similarity` | POST | Find similar clothing items |
| `/match` | POST | Evaluate outfit compatibility |
| `/compute_match` | POST | Compute outfit match score with pre-processed data |
| `/text-search` | POST | Search for clothing items using natural language |
| `/detect-persons` | POST | Detect people in an uploaded image |
| `/health` | GET | Check service health |

### Internal Service Endpoints

| Service | Port | Base URL |
|---------|------|----------|
| External Endpoint Processor | 7000 | http://localhost:7000 |
| Detection IEP | 7001 | http://localhost:7001 |
| Style IEP | 7002 | http://localhost:7002 |
| Feature IEP | 7003 | http://localhost:7003 |
| Virtual Try-On IEP | 7004 | http://localhost:7004 |
| Elegance Fashion Advisor IEP | 7005 | http://localhost:7005 |
| Match IEP | 7008 | http://localhost:7008 |
| Recommendation Data IEP | 7007 | http://localhost:7007 |
| Person Detector IEP | 7009 | http://localhost:7009 |
| Text-to-Image Search IEP | 7020 | http://localhost:7020 |

## Test Images Guidelines

### For Clothing Analysis
- Use clear, well-lit photos of clothing items
- Preferably against a plain background for better detection
- Include various clothing types (shirts, pants, shoes, etc.)
- Resolution should be at least 512x512 pixels

### For Outfit Analysis
- Use full-body photos with multiple visible clothing items
- Use good lighting conditions
- Include a variety of clothing styles and items
- Resolution should be at least 512x768 pixels

## Future Improvements

1. **Backend Database Documentation**: Add setup instructions for MySQL database and Qdrant collection.

2. **Training Scripts**: Include scripts for training or fine-tuning the models.

3. **User Authentication**: Add user accounts and personalized recommendations.

4. **Expanded Fashion Dataset**: Increase the database size for more diverse recommendations.

5. **Mobile Application**: Develop a mobile version of the application.

6. **Offline Mode**: Support limited functionality without external API dependencies.

7. **Batch Processing**: Add support for analyzing multiple images at once.

8. **Swagger Documentation**: Add more comprehensive API documentation.

9. **Vector Database Integration**: Improve integration with Qdrant for faster similarity searches.

## Cleanup

```bash
# Stop all containers
docker-compose down
```

## Acknowledgments

This project uses the following technologies and services:

- [FASHN.AI](https://fashn.ai) for virtual try-on capabilities
- [OpenAI](https://openai.com) for the fashion advisor chatbot
- [YOLOv8](https://github.com/ultralytics/ultralytics) for object detection and segmentation
- [Qdrant](https://qdrant.tech/) for vector similarity search
- [Google Drive API](https://developers.google.com/drive) for image storage

## Project Analysis

### System Architecture Overview

AI Fashion Advisor is built on a robust microservices architecture with 11 specialized services that work together to provide a comprehensive fashion technology solution:

1. **Frontend Interface**: A modern React application serving as the user-facing component
2. **Service Orchestration**: External Endpoint Processor (EEP) that coordinates all service interactions
3. **Computer Vision Pipeline**: Multiple specialized services for clothing detection, feature extraction, and style classification
4. **Virtual Try-On System**: Service for visualizing how clothing items would look on a person
5. **Recommendation Engine**: Services for finding matching or similar clothing items
6. **Outfit Analysis**: Service for evaluating outfit compatibility and providing styling advice
7. **Natural Language Search**: Text-to-Image service for finding clothing by description
8. **Person Detection**: Specialized detection service optimized for identifying people in images
9. **AI Advisor**: Intelligent chatbot service that provides fashion advice and guidance

### Key Technologies

- **Deep Learning**: YOLOv8 for object detection, ResNet50 for feature extraction
- **Vector Databases**: Qdrant for fast similarity search
- **Third-Party APIs**: FASHN.AI for virtual try-on, OpenAI for AI chat capabilities
- **Cloud Storage**: Google Drive for image storage
- **Containerization**: Docker and Docker Compose for deployment
- **Monitoring**: Prometheus metrics integrated across services

### Integration Points

The system integrates with multiple external services:
- API connections to FASHN.AI and OpenAI
- Database connections to MySQL and Qdrant
- File storage on Google Drive
- Azure Key Vault for secrets management
- Azure Blob Storage for model storage

### Data Flow

1. Images are uploaded through the frontend
2. EEP routes requests to appropriate services
3. Detection, classification, and feature extraction are performed
4. Results are processed according to the user's request (recommendations, try-on, matching, etc.)
5. Processed results are returned to the frontend for display

This architecture enables the system to handle complex fashion analysis tasks while maintaining flexibility and scalability.


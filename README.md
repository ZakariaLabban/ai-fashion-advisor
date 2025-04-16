# AI Fashion Advisor

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.10-blue.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18.0-blue.svg)](https://reactjs.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue.svg)](https://docs.docker.com/compose/)

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

## Architecture

The system is built using a microservices architecture with the following components:

1. **React Frontend**: Modern, responsive UI built with React and Tailwind CSS
2. **External Endpoint Processor (EEP)**: Main entry point that coordinates all services
3. **Detection IEP**: Detects clothing items in images using YOLOv8
4. **Feature IEP**: Extracts feature vectors from clothing items with ResNet50
5. **Style IEP**: Classifies clothing styles using a fine-tuned YOLOv8 model
6. **Virtual Try-On IEP**: Enables virtual clothing try-on via FASHN.AI API
7. **Elegance IEP**: AI fashion advisor chatbot built with OpenAI
8. **Recommendation Data IEP**: Provides clothing recommendations and similarity search using vector databases



## Model Files

This project uses several large model files that are not included in the repository:

- `yolov8_clothing_detection_segmentation.pt` - YOLOv8 model for detecting and segmenting clothes
- `yolov8_style_model.pt` - YOLOv8 model for style classification
- `multitask_resnet50_finetuned.pt` - Fine-tuned ResNet50 for feature extraction

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

3. **Create environment files**

   Create a main `.env` file in the root directory:

   ```
   FASHN_AI_API_KEY=your-fashn-api-key-here
   FASHN_AI_BASE_URL=https://api.fashn.ai/v1
   OPENAI_API_KEY=your-openai-api-key-here
   ```

   Create a `.env` file in the `reco_data_iep` directory:

   ```
   MYSQL_HOST=your-mysql-host
   MYSQL_PORT=3306
   MYSQL_USER=username
   MYSQL_PASSWORD=password
   MYSQL_DATABASE=your_database
   MYSQL_SSL_CA=/app/ca.pem

   QDRANT_URL=https://your-qdrant-cloud-url
   QDRANT_API_KEY=your-qdrant-api-key
   COLLECTION_NAME=fashion_features

   SEGMENTED_FOLDER_ID=your_google_drive_folder_id_for_segmented
   FULL_FOLDER_ID=your_google_drive_folder_id_for_full_images
   SERVICE_ACCOUNT_FILE=auradataset-643b5a8d654e.json
   ```

4. **Obtain Google Drive API credentials**

   - Create a service account in Google Cloud Console
   - Download the JSON credentials file and rename it to `auradataset-643b5a8d654e.json`
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

### Fashion Advice

1. Visit the "Elegance Bot" section
2. Chat with the AI advisor for style guidance
3. Ask questions about fashion rules, outfit combinations, or get help with using the system

### Finding Matching or Similar Items

1. Go to the "Recommender" section
2. Upload a clothing item
3. Choose whether to find a matching item (e.g., bottom to match a top) or similar items
4. View the recommended items

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
| Recommendation Data IEP | 7007 | http://localhost:7007 |

## Development

### Frontend Development

```bash
cd frontend
npm install
npm start
```

The development server will run at [http://localhost:5173](http://localhost:5173)

### Adding New Features

1. For new AI models, add them to the appropriate IEP service
2. Update the EEP to expose new endpoints as needed
3. Extend the frontend to support new functionality

### Recommendation Data IEP

The Recommendation Data IEP provides fashion item matching and similarity search:

- **Matching**: Find complementary items (e.g., bottoms to match a top)
- **Similarity**: Find similar items (e.g., similar shirts)

The service integrates:
- **Qdrant Vector Database**: For vector similarity search
- **MySQL Database**: For metadata storage and filtering
- **Google Drive**: For storing and retrieving fashion images

## Known Issues and Limitations

1. **Database Setup**: The recommendation system requires a pre-populated MySQL database and Qdrant collection. Documentation for initial data loading is needed.

2. **Model Availability**: The large model files are not included in the repository and must be obtained separately.

3. **Integration Testing**: Comprehensive end-to-end tests for the complete workflow are missing.

4. **Recommendation Data**: The application needs a significant amount of clothing data to provide meaningful recommendations.

5. **Error Handling**: Some edge cases in the integration between services may not be properly handled.

## Future Improvements

1. **Backend Database Documentation**: Add setup instructions for MySQL database and Qdrant collection.

2. **Training Scripts**: Include scripts for training or fine-tuning the models.

3. **User Authentication**: Add user accounts and personalized recommendations.

4. **Expanded Fashion Dataset**: Increase the database size for more diverse recommendations.

5. **Mobile Application**: Develop a mobile version of the application.

6. **Offline Mode**: Support limited functionality without external API dependencies.

7. **Batch Processing**: Add support for analyzing multiple images at once.

## Cleanup

```bash
# Stop all containers
docker-compose down

# Windows
.\clean.ps1

# Linux/Mac
./clean.sh
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the project
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- FASHN.AI for providing the virtual try-on API
- OpenAI for the conversational AI capabilities
- YOLOv8 and Ultralytics for object detection models
- Qdrant for vector similarity search
- Google Drive for image storage 
# Fashion Analysis with Virtual Try-On

A comprehensive system for fashion item detection, feature extraction, style classification, virtual try-on, and AI fashion advice.

## Architecture

The system consists of several microservices that work together:

1. **React Frontend**: Modern, responsive UI built with React and Tailwind CSS
2. **External Endpoint Processor (EEP)**: Main entry point for the application that coordinates all services
3. **Detection IEP**: Detects clothing items in images
4. **Feature IEP**: Extracts feature vectors from clothing items
5. **Style IEP**: Classifies clothing styles
6. **Virtual Try-On IEP**: Allows trying on clothes virtually using FASHN.AI API
7. **Elegance IEP**: AI fashion advisor chatbot providing style guidance and troubleshooting

## Model Files

This project uses several large model files for clothing detection and feature extraction:

- `yolov8_clothing_detection_segmentation.pt` - YOLOv8 model for detecting clothing items
- `yolov8_style_model.pt` - YOLOv8 model for clothing style classification
- `multitask_resnet50_finetuned.pt` - Custom fine-tuned ResNet50 model for feature extraction

**Note**: These large model files are excluded from Git version control. New users who clone this repository will need to obtain these files separately.

## Prerequisites

- Docker and Docker Compose
- FASHN.AI API key for the virtual try-on functionality
- OpenAI API key for the Elegance chatbot functionality

## Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd fashion-analysis-virtual-tryon
   ```

2. Obtain the required model files and place them in the root directory:
   - `yolov8_clothing_detection_segmentation.pt`
   - `yolov8_style_model.pt`
   - `multitask_resnet50_finetuned.pt`

3. Create a `.env` file in the root directory with your API keys:
   ```
   FASHN_AI_API_KEY=your-fashn-api-key-here
   FASHN_AI_BASE_URL=https://api.fashn.ai/v1
   OPENAI_API_KEY=your-openai-api-key-here
   ```

4. Build and start the Docker containers:
   ```bash
   docker-compose up -d
   ```

## Usage

Once all services are running, you can access the system through the modern React frontend at `http://localhost:3000/` or the original web interface at `http://localhost:7000/`.

### Modern React Frontend

The React frontend provides a modern, responsive interface with the following features:
- **Home**: Landing page with hero section and featured services
- **Analyze Your Fit**: Upload and analyze clothing items
- **Fitting Room**: Virtual try-on functionality
- **Elegance Bot**: Fashion advice chatbot

### Clothing Analysis

1. Upload an image containing clothing items.
2. The system will detect clothing items, extract features, and classify styles.
3. Results will be displayed with bounding boxes around detected items.

### Virtual Try-On

1. Navigate to the Fitting Room section in the interface.
2. Upload a model image (person).
3. Upload a garment image (clothing item).
4. Click "Try On Garment" to see the garment on the model.

### Fashion Advisor Chatbot

1. Navigate to the Elegance Bot section.
2. Chat with Elegance, the French fashion advisor AI, to get style advice.
3. Ask about fashion rules, outfit combinations, or troubleshooting help with the system.

## API Endpoints

### EEP Endpoints

- `POST /analyze`: Analyze clothing in an uploaded image
- `POST /tryon`: Virtual try-on with a model and a garment
- `POST /tryon/multi`: Try on multiple garments (top and bottom)
- `GET /elegance`: Access the Elegance fashion advisor chatbot
- `POST /api/elegance/chat`: API endpoint for the Elegance chatbot
- `GET /health`: Check service health

### IEP Endpoints

- Detection IEP: `http://localhost:7001/`
- Style IEP: `http://localhost:7002/`
- Feature IEP: `http://localhost:7003/`
- Virtual Try-On IEP: `http://localhost:7004/`
- Elegance Fashion Advisor IEP: `http://localhost:7005/`

## Frontend Development

The React frontend is located in the `frontend` directory. To develop the frontend independently:

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm start
   ```

4. Access the frontend at `http://localhost:5173`

## Git Version Control

This project is configured for Git with appropriate `.gitignore` settings. When working with this repository:

1. Large model files (*.pt) are excluded from version control
2. The `.env` file containing API keys is excluded
3. Uploaded images and results in static directories are excluded

After cloning, you'll need to:
- Obtain the model files separately
- Create a `.env` file with your API keys
- Create empty directories for uploads and results if they don't exist

## Cleaning Up

To remove all containers and networks:
```bash
docker-compose down
```

To also remove all generated images and uploaded files:
- On Windows: `.\clean.ps1`
- On Linux/Mac: `./clean.sh`

## License

[License information] 
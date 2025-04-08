# AURAI Fashion Advisor Frontend

This frontend application provides a modern, responsive user interface for the AURAI Fashion Advisor system using React and Tailwind CSS.

## Features

- **Modern UI**: Clean, responsive design built with Tailwind CSS
- **Analyze Your Fit**: Upload and analyze your outfit
- **Virtual Fitting Room**: Try on garments virtually
- **Elegance Bot**: AI-powered fashion advice chatbot
- **Mobile-friendly**: Fully responsive design for all screen sizes

## Technology Stack

- React 18
- Tailwind CSS
- Vite (for build and development)
- Axios (for API requests)
- React Router (for navigation)
- Font Awesome (for icons)

## Getting Started

### Development

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm start
```

3. Open your browser and navigate to `http://localhost:5173`

### Production Build

```bash
npm run build
```

This will create an optimized production build in the `dist` folder.

## Docker

This application is designed to be run with Docker. The included Dockerfile creates an optimized production build and serves it using NGINX.

### Building and Running with Docker

```bash
docker build -t aurai-frontend .
docker run -p 3000:80 aurai-frontend
```

## Docker Compose

The application is integrated into the overall AURAI Fashion Advisor system through Docker Compose. To run the entire system:

```bash
docker-compose up -d
```

This will build and start all services, including the frontend, which will be available at `http://localhost:3000`.

## API Integration

The frontend communicates with the following API endpoints:

- `/analyze` - For outfit analysis
- `/api/tryon` - For virtual try-on functionality
- `/api/elegance/chat` - For the chatbot

NGINX is configured to proxy these requests to the appropriate backend services. 
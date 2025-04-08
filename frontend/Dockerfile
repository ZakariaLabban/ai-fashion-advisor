FROM node:18-alpine as build

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy all files
COPY . .

# Build the application
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built assets from build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Copy custom nginx config to properly handle SPA routing
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Create startup script with proper line endings
RUN echo '#!/bin/sh' > /docker-entrypoint.sh && \
    echo 'mkdir -p /usr/share/nginx/html/static/uploads' >> /docker-entrypoint.sh && \
    echo 'mkdir -p /usr/share/nginx/html/static/results' >> /docker-entrypoint.sh && \
    echo 'exec nginx -g "daemon off;"' >> /docker-entrypoint.sh && \
    chmod +x /docker-entrypoint.sh

# Expose port
EXPOSE 80

CMD ["/docker-entrypoint.sh"] 
# Multi-stage build for minimal image size
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend

# Accept build argument for API base URL
ARG VITE_API_BASE=http://localhost:8000

# Copy frontend package files
COPY frontend/package*.json ./

# Install frontend dependencies (including dev dependencies for build)
RUN npm ci

# Copy frontend source code
COPY frontend/ ./

# Set environment variable for Vite build
ENV VITE_API_BASE=${VITE_API_BASE}

# Build frontend static files
RUN npm run build

# Python backend stage
FROM python:3.12-alpine AS backend

WORKDIR /app

# Install system dependencies for Python packages
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    && rm -rf /var/cache/apk/*

# Copy backend requirements and install Python dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY backend/ ./

# Copy built frontend static files to serve via FastAPI
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Create non-root user for security
RUN addgroup -g 1001 -S appgroup && \
    adduser -S appuser -u 1001 -G appgroup

# Create data directory and set proper ownership
RUN mkdir -p data && \
    chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

# Expose FastAPI port
EXPOSE 8000

# Start FastAPI server
CMD ["python", "main.py"]

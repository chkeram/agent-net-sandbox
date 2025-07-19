# Template Dockerfile for agents
# Customize based on your technology stack

# Choose appropriate base image
FROM python:3.11-slim
# FROM node:18-alpine
# FROM golang:1.21-alpine
# FROM rust:1.70

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set work directory
WORKDIR /app

# Install system dependencies (customize based on needs)
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files first for better caching
COPY requirements.txt .
# COPY package.json package-lock.json ./  # For Node.js
# COPY go.mod go.sum ./                   # For Go
# COPY Cargo.toml Cargo.lock ./           # For Rust

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt
# RUN npm ci --only=production            # For Node.js
# RUN go mod download                     # For Go  
# RUN cargo build --release               # For Rust

# Copy source code
COPY src/ ./src/
# COPY . .                                # For other languages

# Create non-root user for security
RUN adduser --disabled-password --gecos '' --shell /bin/bash agentuser \
    && chown -R agentuser:agentuser /app
USER agentuser

# Expose the port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Set environment variables for your app
ENV PYTHONPATH=/app/src
# ENV NODE_ENV=production                 # For Node.js
# ENV RUST_LOG=info                       # For Rust

# Command to run the application
CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
# CMD ["npm", "start"]                    # For Node.js
# CMD ["node", "src/app.js"]              # For Node.js
# CMD ["./main"]                          # For Go
# CMD ["./target/release/app"]            # For Rust
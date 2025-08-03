---
title: "Building Development Environment with Docker"
meta_title: ""
description: "Learn how to build consistent development environments using Docker and container-based development workflows."
date: 2025-07-30T11:20:00Z
image: "/images/service-1.png"
categories: ["DevOps", "Container"]
author: "Kigo"
tags: ["Docker", "DevOps", "Container", "Development Environment"]
draft: false
---

During development, you often hear "It worked on my machine!" Docker can solve this problem and help build consistent development environments.

## What is Docker?

Docker is a container-based virtualization platform. You can package applications and everything needed to run them into a single container.

### Advantages of Docker

- **Consistency**: Same environment anywhere
- **Isolation**: Each container runs independently
- **Portability**: Can run on any platform
- **Efficiency**: Lighter than virtual machines

## Basic Docker Commands

### Image Management

```bash
# Search for images
docker search nginx

# Pull images
docker pull nginx:latest

# List images
docker images

# Remove images
docker rmi nginx:latest
```

### Container Management

```bash
# Run container
docker run -d --name web-server -p 8080:80 nginx

# List containers
docker ps -a

# Stop container
docker stop web-server

# Start container
docker start web-server

# Remove container
docker rm web-server
```

## Dockerfile

Create custom images using Dockerfile:

```dockerfile
# Base image
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Expose port
EXPOSE 3000

# Start command
CMD ["npm", "start"]
```

## Docker Compose

Manage multi-container applications:

```yaml
version: '3.8'
services:
  web:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=development
    volumes:
      - .:/app
      - /app/node_modules
    depends_on:
      - database

  database:
    image: postgres:14
    environment:
      POSTGRES_DB: myapp
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres_data:
```

## Development Environment Setup

### 1. Node.js Project

```bash
# Create project directory
mkdir my-node-app && cd my-node-app

# Create Dockerfile
cat > Dockerfile << EOF
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 3000
CMD ["npm", "run", "dev"]
EOF

# Create docker-compose.yml
cat > docker-compose.yml << EOF
version: '3.8'
services:
  app:
    build: .
    ports:
      - "3000:3000"
    volumes:
      - .:/app
      - /app/node_modules
    environment:
      - NODE_ENV=development
EOF

# Start development environment
docker-compose up
```

### 2. Java Spring Boot Project

```dockerfile
FROM openjdk:17-jdk-slim

WORKDIR /app

COPY pom.xml .
COPY .mvn .mvn
COPY mvnw .

RUN chmod +x mvnw && ./mvnw dependency:go-offline

COPY src ./src

EXPOSE 8080

CMD ["./mvnw", "spring-boot:run"]
```

## Best Practices

### 1. .dockerignore

```dockerignore
node_modules
npm-debug.log
.git
.gitignore
README.md
.env
.nyc_output
coverage
.tmp
```

### 2. Multi-stage Build

```dockerfile
# Build stage
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

# Production stage
FROM node:18-alpine
WORKDIR /app
COPY --from=builder /app/node_modules ./node_modules
COPY . .
EXPOSE 3000
CMD ["node", "server.js"]
```

### 3. Health Checks

```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:3000/health || exit 1
```

## Development Workflow

### 1. Code → Build → Test → Deploy

```bash
# Build image
docker build -t myapp:latest .

# Run tests
docker run --rm myapp:latest npm test

# Deploy to staging
docker run -d --name staging-app -p 3001:3000 myapp:latest
```

### 2. CI/CD Pipeline

```yaml
# .github/workflows/docker.yml
name: Docker Build and Deploy

on:
  push:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Build Docker image
      run: docker build -t myapp .

    - name: Run tests
      run: docker run --rm myapp npm test

    - name: Deploy to production
      run: |
        docker tag myapp myregistry/myapp:latest
        docker push myregistry/myapp:latest
```

## Troubleshooting

### Common Issues

1. **Port conflicts**
   ```bash
   # Check port usage
   lsof -i :3000

   # Use different port
   docker run -p 3001:3000 myapp
   ```

2. **Volume mount issues**
   ```bash
   # Check volume mounts
   docker inspect container_name

   # Fix permissions
   docker run --user $(id -u):$(id -g) myapp
   ```

3. **Network issues**
   ```bash
   # Create custom network
   docker network create mynetwork

   # Run containers on same network
   docker run --network mynetwork myapp
   ```

## Conclusion

Docker greatly improves development productivity by providing consistent environments. Start with simple Dockerfile and docker-compose.yml files, then gradually adopt more advanced features.

In the next post, we'll explore Kubernetes orchestration and container deployment strategies.

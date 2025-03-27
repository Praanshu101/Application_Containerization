# Application Containerization Project

## Overview
This project demonstrates containerization of a FastAPI application with Elasticsearch backend using Docker.

## Components
- **Frontend**: A FastAPI service serving a web interface for user interaction
- **Backend**: A FastAPI API service interacting with Elasticsearch
- **Elasticsearch**: Document storage and search engine

## Setup and Running

### Prerequisites
- Docker and Docker Compose installed
- At least 4GB of RAM available for Docker

### Starting the Application

1. Clone the repository
2. Navigate to the project directory
3. Run the following command:

```bash
docker-compose up --build
```

### Accessing the Application

- Frontend interface: http://localhost:9567
- Backend API: http://localhost:8000
- Elasticsearch: http://localhost:9200

### Testing

To run tests:

```bash
docker-compose run backend pytest
```

## Troubleshooting

If Elasticsearch fails to start, try:

1. Increase Docker memory allocation (minimum 4GB recommended)
2. Clear Docker volumes:
   ```bash
   docker-compose down -v
   ```
3. Rebuild and restart:
   ```bash
   docker-compose up --build
   ```

## Architecture
- Frontend service (port 9567) - User interface
- Backend service (port 8000) - API handling
- Elasticsearch (port 9200) - Document storage and search
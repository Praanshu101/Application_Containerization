from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from elasticsearch import Elasticsearch, ConnectionTimeout, ConnectionError
from pydantic import BaseModel
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import os
import time
import logging
import sys

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler(sys.stdout)])
logger = logging.getLogger("main")

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins in development
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Get Elasticsearch URL and timeout from environment variables
ELASTICSEARCH_URL = os.environ.get("ELASTICSEARCH_URL", "http://elasticsearch:9200")
ELASTICSEARCH_TIMEOUT = int(os.environ.get("ELASTICSEARCH_TIMEOUT", "30"))
ELASTICSEARCH_URL = os.getenv('ELASTICSEARCH_URL', 'http://elasticsearch:9200')

# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "ok"}

# ES status endpoint
@app.get("/es-status")
def es_status():
    try:
        es = Elasticsearch([ELASTICSEARCH_URL], timeout=10)
        if es.ping():
            return {"status": "Elasticsearch is available", "info": es.info()}
        else:
            raise HTTPException(status_code=503, detail="Elasticsearch is not responding")
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Error connecting to Elasticsearch: {str(e)}")

# Improved connection handling

def create_elasticsearch_client(max_retries=30, retry_delay=5):
    """
    Create an Elasticsearch client with robust connection handling
    
    Args:
        max_retries (int): Number of connection attempts
        retry_delay (int): Seconds between retry attempts
    
    Returns:
        Elasticsearch client or raises ValueError
    """
    for attempt in range(max_retries):
        try:
            print(f"Attempting Elasticsearch connection (Attempt {attempt + 1})...")
            es = Elasticsearch([ELASTICSEARCH_URL], 
                               connection_attempts=3, 
                               retry_on_timeout=True)
            
            # More comprehensive health check
            health = es.cluster.health(wait_for_status='yellow', timeout='30s')
            
            if health['status'] in ['green', 'yellow']:
                print(f"Successfully connected to Elasticsearch. Cluster status: {health['status']}")
                return es
            
        except Exception as e:
            print(f"Connection attempt failed: {e}")
            time.sleep(retry_delay)
    
    raise ValueError("Could not establish connection to Elasticsearch after maximum retries")

# Use this function when initializing your Elasticsearch client
es = create_elasticsearch_client()
_es_client = None

def get_es_client():
    global _es_client
    if _es_client is None:
        _es_client = connect_to_elasticsearch()
    return _es_client

# Pydantic model
class Document(BaseModel):
    id: Optional[str] = None
    text: str

INDEX_NAME = "documents"

# Initialize the index when app starts
@app.on_event("startup")
async def startup_db_client():
    try:
        es = get_es_client()
        
        # Create index if it doesn't exist
        if not es.indices.exists(index=INDEX_NAME):
            logger.info(f"Creating index '{INDEX_NAME}'")
            es.indices.create(index=INDEX_NAME, body={
                "mappings": {
                    "properties": {
                        "id": {"type": "keyword"},
                        "text": {"type": "text"}
                    }
                }
            })
            logger.info(f"Index '{INDEX_NAME}' created successfully")
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        # Don't fail startup - we'll retry on first request

# API endpoints
@app.post("/documents/", response_model=Document)
def create_document(document: Document):
    es = get_es_client()
    result = es.index(index=INDEX_NAME, body=document.dict())
    document.id = result["_id"]
    return document

@app.get("/documents/{document_id}", response_model=Document)
def read_document(document_id: str):
    es = get_es_client()
    try:
        result = es.get(index=INDEX_NAME, id=document_id)
        return Document(**result["_source"], id=result["_id"])
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Document not found: {str(e)}")

@app.get("/documents/", response_model=list[Document])
def search_documents(q: Optional[str] = None):
    es = get_es_client()
    
    if q:
        query = {
            "query": {
                "match": {
                    "text": q
                }
            }
        }
    else:
        query = {
            "query": {
                "match_all": {}
            }
        }
    
    results = es.search(index=INDEX_NAME, body=query)
    documents = []
    for hit in results["hits"]["hits"]:
        documents.append(Document(**hit["_source"], id=hit["_id"]))
    return documents

@app.put("/documents/{document_id}", response_model=Document)
def update_document(document_id: str, document: Document):
    es = get_es_client()
    result = es.update(index=INDEX_NAME, id=document_id, body={"doc": document.dict(exclude={"id"})})
    document.id = document_id
    return document

@app.delete("/documents/{document_id}")
def delete_document(document_id: str):
    es = get_es_client()
    es.delete(index=INDEX_NAME, id=document_id)
    return {"message": f"Document {document_id} deleted successfully"}

@app.get("/favicon.ico")
def favicon():
    return FileResponse("static/favicon.ico")

# Mount the static folder for frontend
app.mount("/", StaticFiles(directory="static", html=True), name="static")

import uvicorn
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

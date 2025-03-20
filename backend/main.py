from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from elasticsearch import Elasticsearch
from pydantic import BaseModel
from fastapi.responses import FileResponse

app = FastAPI()

# Connect to Elasticsearch inside Docker
#es = Elasticsearch("http://elasticsearch:9567")

import time
#from elasticsearch import Elasticsearch

ELASTICSEARCH_URL = "http://elasticsearch:9567"

for _ in range(10):  # Retry up to 10 times
    try:
        es = Elasticsearch([ELASTICSEARCH_URL])
        if es.ping():
            print("Connected to Elasticsearch")
            break
    except Exception as e:
        print("Retrying Elasticsearch connection...")
        time.sleep(5)
else:
    raise ValueError("Elasticsearch is not available")

INDEX_NAME = "documents"

# Ensure the index exists
if not es.indices.exists(index=INDEX_NAME).body:  
    es.indices.create(index=INDEX_NAME, body={
        "mappings": {
            "properties": {
                "id": {"type": "keyword"},
                "text": {"type": "text"}
            }
        }
    })

# Insert 4 initial documents into Elasticsearch
docs = [
    {"id": "1", "text": "India is a country in South Asia."},
    {"id": "2", "text": "It is the seventh-largest country by land area."},
    {"id": "3", "text": "India has a rich cultural heritage."},
    {"id": "4", "text": "New Delhi is the capital city of India."},
]

for doc in docs:
    es.index(index=INDEX_NAME, id=doc["id"], body=doc)  

# Pydantic model for inserting a document
class Document(BaseModel):
    text: str


@app.get("/search/")
def search(query: str):
    """Search for documents in Elasticsearch"""
    result = es.search(index=INDEX_NAME, body={
        "query": {
            "match": {"text": query}
        }
    })
    return result["hits"]["hits"]


@app.post("/insert/")
def insert_document(doc: Document):
    """Insert a new document into Elasticsearch"""
    new_id = str(es.count(index=INDEX_NAME)["count"] + 1)  
    new_doc = {"id": new_id, "text": doc.text}
    es.index(index=INDEX_NAME, id=new_id, body=new_doc)  
    return {"status": "Inserted", "document": new_doc}

@app.get("/favicon.ico")
def favicon():
    return FileResponse("static/favicon.ico")

# Mount the static folder for frontend
app.mount("/", StaticFiles(directory="static", html=True), name="static")

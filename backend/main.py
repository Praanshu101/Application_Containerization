from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from elasticsearch import Elasticsearch
from pydantic import BaseModel
from fastapi.responses import FileResponse
from typing import Optional

app = FastAPI()

# Connect to Elasticsearch inside Docker
#es = Elasticsearch("http://elasticsearch:9567")

import time
#from elasticsearch import Elasticsearch

ELASTICSEARCH_URL = "http://elasticsearch:9567"

for _ in range(30):  # Retry up to 10 times
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
if not es.indices.exists(index=INDEX_NAME):  
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
    {"id": "1", "text": "India, officially the Republic of India,[j][21] is a country in South Asia. It is the seventh-largest country by area; the most populous country from June 2023 onwards;[22][23] and since its independence in 1947, the world's most populous democracy.[24][25][26] Bounded by the Indian Ocean on the south, the Arabian Sea on the southwest, and the Bay of Bengal on the southeast, it shares land borders with Pakistan to the west;[k] China, Nepal, and Bhutan to the north; and Bangladesh and Myanmar to the east. In the Indian Ocean, India is near Sri Lanka and the Maldives; its Andaman and Nicobar Islands share a maritime border with Thailand, Myanmar, and Indonesia."},
    {"id": "2", "text": "Modern humans arrived on the Indian subcontinent from Africa no later than 55,000 years ago.[28][29][30] Their long occupation, predominantly in isolation as hunter-gatherers, has made the region highly diverse, second only to Africa in human genetic diversity.[31] Settled life emerged on the subcontinent in the western margins of the Indus river basin 9,000 years ago, evolving gradually into the Indus Valley Civilisation of the third millennium BCE.[32] By 1200 BCE, an archaic form of Sanskrit, an Indo-European language, had diffused into India from the northwest.[33][34] Its hymns recorded the dawning of Hinduism in India.[35] India's pre-existing Dravidian languages were supplanted in the northern regions.[36] By 400 BCE, caste had emerged within Hinduism,[37] and Buddhism and Jainism had arisen, proclaiming social orders unlinked to heredity.[38] Early political consolidations gave rise to the loose-knit Maurya and Gupta Empires.[39] Widespread creativity suffused this era,[40] but the status of women declined,[41] and untouchability became an organized belief.[l][42] In South India, the Middle kingdoms exported Dravidian language scripts and religious cultures to the kingdoms of Southeast Asia.[43]"},
    {"id": "3", "text": "In the early mediaeval era, Christianity, Islam, Judaism, and Zoroastrianism became established on India's southern and western coasts.[44] Muslim armies from Central Asia intermittently overran India's northern plains.[45] The resulting Delhi Sultanate drew northern India into the cosmopolitan networks of mediaeval Islam.[46] In south India, the Vijayanagara Empire created a long-lasting composite Hindu culture.[47] In the Punjab, Sikhism emerged, rejecting institutionalised religion.[48] The Mughal Empire, in 1526, ushered in two centuries of relative peace,[49] leaving a legacy of luminous architecture.[m][50] Gradually expanding rule of the British East India Company turned India into a colonial economy but consolidated its sovereignty.[51] British Crown rule began in 1858. The rights promised to Indians were granted slowly,[52][53] but technological changes were introduced, and modern ideas of education and public life took root.[54] A pioneering and influential nationalist movement, noted for nonviolent resistance, became the major factor in ending British rule.[55][56] In 1947, the British Indian Empire was partitioned into two independent dominions,[57][58][59][60] a Hindu-majority dominion of India and a Muslim-majority dominion of Pakistan. A large-scale loss of life and an unprecedented migration accompanied the partition.[61]"},
    {"id": "4", "text": "India has been a federal republic since 1950, governed through a democratic parliamentary system. It is a pluralistic, multilingual and multi-ethnic society. India's population grew from 361 million in 1951 to over 1.4 billion in 2023.[62] During this time, its nominal per capita income increased from US$64 annually to US$2,601, and its literacy rate from 16.6% to 74%. A comparatively destitute country in 1951,[63] India has become a fast-growing major economy and hub for information technology services; it has an expanding middle class.[64] Indian movies and music increasingly influence global culture.[65] India has reduced its poverty rate, though at the cost of increasing economic inequality.[66] It is a nuclear-weapon state that ranks high in military expenditure. It has disputes over Kashmir with its neighbours, Pakistan and China, unresolved since the mid-20th century.[67] Among the socio-economic challenges India faces are gender inequality, child malnutrition,[68] and rising levels of air pollution.[69] India's land is megadiverse with four biodiversity hotspots.[70] India's wildlife, which has traditionally been viewed with tolerance in its culture,[71] is supported in protected habitats."},
]

for doc in docs:
    es.index(index=INDEX_NAME, id=doc["id"], body=doc)  

# Pydantic model for inserting a document
class Document(BaseModel):
    text: str

@app.get("/messages")
def get_messages():
    """Return all documents to match frontend expectations"""
    try:
        result = es.search(index=INDEX_NAME, body={
            "query": {"match_all": {}}
        })
        
        messages = {}
        for hit in result["hits"]["hits"]:
            doc = hit["_source"]
            # Use get() with fallback to avoid KeyError
            doc_id = doc.get("id", hit["_id"])
            try:
                # Convert to int safely
                msg_id = int(doc_id)
            except ValueError:
                # Fallback if ID can't be converted to int
                msg_id = 0
                
            messages[doc_id] = {"msg_id": msg_id, "msg_name": doc["text"]}
        
        # Debugging - log what we're returning
        print(f"Returning messages: {messages}")
        return {"messages": messages}
    except Exception as e:
        # Log the error and return empty result
        print(f"Error in get_messages: {str(e)}")
        return {"messages": {}, "error": str(e)}

@app.post("/messages/{text}/")
def add_message(text: str):
    """Insert a message from URL path parameter to match frontend expectations"""
    result = es.index(index=INDEX_NAME, body={"text": text})
    new_id = result["_id"]
    new_doc = {"id": new_id, "text": text}
    return {"status": "Inserted", "document": new_doc}


@app.get("/search/")
def search(query: str):
    """Search for documents in Elasticsearch"""
    result = es.search(index=INDEX_NAME, body={
        "query": {
            "match": {"text": query}
        }
    })
    
    # Format the response to match frontend expectations
    messages = {}
    for hit in result["hits"]["hits"]:
        doc = hit["_source"]
        doc_id = doc.get("id", hit["_id"])
        messages[doc_id] = {"msg_id": int(doc_id), "msg_name": doc["text"]}
    
    return {"messages": messages}


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

@app.get("/get")
def get_documents(query: Optional[str] = None):
    """Return documents matching query or all if no query provided"""
    try:
        # Use query if provided, otherwise match_all
        if query:
            print(f"Searching for query: '{query}'")
            search_body = {
                "query": {
                    "match": {"text": query}
                }
            }
        else:
            print("No query provided, returning all documents")
            search_body = {
                "query": {"match_all": {}}
            }
            
        # Execute search and get all matching documents
        result = es.search(index=INDEX_NAME, body=search_body, size=100)  # Get up to 100 docs
        
        # Format results
        messages = {}
        for hit in result["hits"]["hits"]:
            doc = hit["_source"]
            doc_id = doc.get("id", hit["_id"])
            score = hit["_score"]
            
            try:
                msg_id = int(doc_id)
            except ValueError:
                msg_id = doc_id  # Keep as string if can't convert
                
            messages[doc_id] = {
                "msg_id": msg_id, 
                "msg_name": doc["text"],
                "score": score
            }
        
        # Debugging
        print(f"Returning {len(messages)} documents for query: {query or 'None'}")
        return {"messages": messages}
    except Exception as e:
        print(f"Error in get_documents: {str(e)}")
        return {"messages": {}, "error": str(e)}

@app.get("/es-status")
def es_status():
    """Check Elasticsearch connection status"""
    try:
        health = es.cluster.health()
        indices = es.cat.indices(format="json")
        doc_count = es.count(index=INDEX_NAME)
        return {
            "status": "connected",
            "health": health,
            "indices": indices,
            "document_count": doc_count
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

# Mount the static folder for frontend
# app.mount("/", StaticFiles(directory="static", html=True), name="static")
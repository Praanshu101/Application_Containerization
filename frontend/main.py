from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.responses import RedirectResponse
import requests

app = FastAPI()

# Serve static files (including index.html)
app.mount("/static", StaticFiles(directory="static", html=True), name="static")

# Redirect root URL to index.html
@app.get("/")
def read_root():
    return RedirectResponse(url="/static/index.html")

# Backend URL (assuming container network setup)
BACKEND_URL = "http://backend:9567"

# Route for retrieving the best-scoring document
@app.get("/get")
def get_best_document():
    try:
        response = requests.get(f"{BACKEND_URL}/messages")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

# Route for inserting a document
@app.post("/insert/{text}")
def insert_document(text: str):
    try:
        response = requests.post(f"{BACKEND_URL}/messages/{text}/")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

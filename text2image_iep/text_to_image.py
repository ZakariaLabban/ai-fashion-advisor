from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from transformers import CLIPProcessor, CLIPModel
from qdrant_client import QdrantClient
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import torch
import io
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()

# === Load CLIP model and processor ===
clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32", cache_dir="./models")
clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32", cache_dir="./models")

def get_text_embedding(text: str):
    inputs = clip_processor(text=[text], return_tensors="pt")
    with torch.no_grad():
        embedding = clip_model.get_text_features(**inputs)
        embedding = embedding / embedding.norm(dim=-1, keepdim=True)
    return embedding[0].cpu().tolist()

# === Connect to Qdrant ===
qdrant = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY")
)
COLLECTION = "text-to-image"

# === Authenticate with Google Drive ===
SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
FOLDER_ID = os.getenv("GOOGLE_FOLDER_ID")
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
drive_service = build('drive', 'v3', credentials=credentials)

def get_file_id_by_filename(filename: str) -> str:
    query = f"name = '{filename}' and '{FOLDER_ID}' in parents"
    response = drive_service.files().list(q=query, fields="files(id)").execute()
    files = response.get("files", [])
    if not files:
        return None
    return files[0]["id"]

def stream_image_from_drive(file_id: str):
    request = drive_service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    fh.seek(0)
    return fh

# === Request Schema ===
class SearchRequest(BaseModel):
    query: str

@app.post("/text-search")
def stream_top_match(request: SearchRequest):
    try:
        # Step 1: Encode text
        query_vector = get_text_embedding(request.query)

        # Step 2: Qdrant Search
        results = qdrant.search(
            collection_name=COLLECTION,
            query_vector=query_vector,
            limit=1,
            with_payload=True
        )

        if not results:
            raise HTTPException(status_code=404, detail="No match found.")

        # Step 3: Convert to filename
        image_id = results[0].payload["image_id"]
        filename = f"{image_id}.jpg"

        # Step 4: Query Drive
        file_id = get_file_id_by_filename(filename)
        if not file_id:
            raise HTTPException(status_code=404, detail=f"File '{filename}' not found in Drive.")

        # Step 5: Stream image back
        image_bytes = stream_image_from_drive(file_id)
        return StreamingResponse(image_bytes, media_type="image/jpeg")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test Qdrant connectivity
        qdrant.get_collection(collection_name=COLLECTION)
        
        # Test Drive API
        drive_service.files().list(q=f"'{FOLDER_ID}' in parents", pageSize=1).execute()
        
        return {
            "status": "healthy", 
            "service": "Text to Image IEP",
            "models": ["CLIP-ViT-B/32"],
            "collections": [COLLECTION]
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

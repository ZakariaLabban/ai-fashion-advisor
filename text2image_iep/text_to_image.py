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
import openai
import json

load_dotenv()

app = FastAPI()

# === Configure OpenAI ===
openai.api_key = os.getenv("OPENAI_API_KEY")

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

# === Check if query is clothing-related ===
async def is_clothing_related(query: str) -> bool:
    try:
        # List of non-clothing related keywords that should be blocked
        blocked_keywords = [
            "car", "cars", "vehicle", "animal", "dog", "cat", "food", "fruit", 
            "vegetable", "computer", "laptop", "phone", "technology", "building", 
            "house", "landscape", "nature", "abstract", "politics", "religion",
            "medical", "weapon", "game", "sports"
        ]
        
        # Quick check for obvious non-clothing items
        query_lower = query.lower()
        for keyword in blocked_keywords:
            if keyword in query_lower:
                print(f"Blocked query containing keyword: {keyword}")
                return False
        
        # Use OpenAI for more nuanced checks
        prompt = f"""
        Determine if the following query is related to clothing or fashion items.
        
        Query: "{query}"
        
        Answer with ONLY "yes" if the query is clearly about clothing items or fashion (like shirts, dresses, pants, shoes, etc.), 
        and "no" for anything else (like food, animals, technology, nature, etc.).
        """
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a strict fashion assistant that only approves queries related to clothing items."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=10
            )
            
            answer = response.choices[0].message.content.strip().lower()
            print(f"OpenAI check for '{query}': {answer}")
            return "yes" in answer
        except Exception as e:
            print(f"Error in OpenAI check: {str(e)}")
            
            # Fallback to a more robust keyword check if OpenAI fails
            clothing_keywords = [
                "shirt", "dress", "pants", "jeans", "skirt", "jacket", "coat", "sweater", 
                "hoodie", "t-shirt", "tshirt", "blouse", "top", "shorts", "trousers", 
                "shoes", "boots", "sneakers", "heels", "sandals", "hat", "cap", "scarf", 
                "gloves", "socks", "underwear", "suit", "tuxedo", "gown", "outfit", 
                "fashion", "clothing", "apparel", "garment", "wear", "attire", "style"
            ]
            
            # Check if any clothing keyword is in the query
            for keyword in clothing_keywords:
                if keyword in query_lower:
                    print(f"Allowing query containing clothing keyword: {keyword}")
                    return True
                    
            # If no clothing keywords found, reject the query
            print(f"No clothing keywords found in query: {query}")
            return False
    except Exception as e:
        print(f"Critical error in clothing check: {str(e)}")
        # In case of any exception, be strict and return False to prevent non-clothing queries
        return False

# === Request Schema ===
class SearchRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    is_clothing_related: bool
    message: str

@app.post("/text-search")
async def stream_top_match(request: SearchRequest):
    try:
        # Step 0: Check if query is clothing-related
        is_related = await is_clothing_related(request.query)
        
        if not is_related:
            print(f"Rejected non-clothing query: '{request.query}'")
            raise HTTPException(
                status_code=400, 
                detail="Your query doesn't appear to be related to clothing or fashion. Please try a fashion-related query."
            )
        
        print(f"Processing clothing-related query: '{request.query}'")
        
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
        print(f"Found image match for query: '{request.query}'")
        image_bytes = stream_image_from_drive(file_id)
        return StreamingResponse(image_bytes, media_type="image/jpeg")

    except HTTPException as e:
        print(f"HTTP Exception during image search: {e.detail}")
        raise e
    except Exception as e:
        print(f"Unexpected error during image search: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/check-query")
async def check_clothing_query(request: SearchRequest):
    """Endpoint to check if a query is clothing-related without performing the image search"""
    try:
        print(f"Checking if query is clothing-related: '{request.query}'")
        is_related = await is_clothing_related(request.query)
        
        if is_related:
            print(f"Query is clothing-related: '{request.query}'")
            return {"is_clothing_related": True, "message": "Query is related to clothing or fashion."}
        else:
            print(f"Query is NOT clothing-related: '{request.query}'")
            return {"is_clothing_related": False, "message": "Query is not related to clothing or fashion."}
    except Exception as e:
        print(f"Error checking query: {str(e)}")
        # In case of any exception, assume it's not clothing-related to be safe
        return {"is_clothing_related": False, "message": f"Error checking query: {str(e)}"}

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

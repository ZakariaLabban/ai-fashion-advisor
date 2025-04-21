from fastapi import FastAPI, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
import mysql.connector
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct, Filter, FieldCondition, MatchValue
import numpy as np
import io
from fastapi.responses import StreamingResponse, PlainTextResponse
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2.service_account import Credentials
import uvicorn
from qdrant_client.http.models import MatchAny
from dotenv import load_dotenv
import os
import logging
import time
# Import Prometheus client for metrics
from prometheus_client import Counter, Histogram, Gauge, generate_latest

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()  # Load from .env file

def find_file_id_in_drive(file_name: str, folder_id: str):
    query = f"name = '{file_name}' and '{folder_id}' in parents and trashed = false"
    results = drive_service.files().list(q=query, fields="files(id)").execute()
    files = results.get("files", [])
    return files[0]["id"] if files else None

def build_qdrant_filter(filters_dict: Optional[dict]):
    if not filters_dict:
        return None

    conditions = []
    
    # Only filter by segmented_pic_ids
    if "segmented_pic_ids" in filters_dict:
        ids = filters_dict["segmented_pic_ids"]
        if isinstance(ids, list) and len(ids) > 0:
            conditions.append(FieldCondition(
                key="segmented_pic_id",
                match=MatchAny(any=ids)
            ))

    return Filter(must=conditions) if conditions else None


# === FastAPI Init ===
app = FastAPI(title="Recommendation IEP", version="1.0")

# === Prometheus Metrics ===
RECO_REQUESTS = Counter(
    'recommendation_requests_total', 
    'Total number of recommendation requests processed'
)
RECO_ERRORS = Counter(
    'recommendation_errors_total', 
    'Total number of errors during recommendation processing'
)
RECO_PROCESSING_TIME = Histogram(
    'recommendation_processing_seconds', 
    'Time spent processing recommendation requests',
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
)
MATCHING_REQUESTS = Counter(
    'matching_requests_total',
    'Total number of matching requests processed'
)
SIMILARITY_REQUESTS = Counter(
    'similarity_requests_total',
    'Total number of similarity requests processed'
)
DB_CONNECTION_ERRORS = Counter(
    'db_connection_errors_total',
    'Total number of database connection errors'
)

# === Configs ===
MYSQL_CONFIG = {
    "host": os.getenv("MYSQL_HOST"),
    "port": int(os.getenv("MYSQL_PORT")),
    "user": os.getenv("MYSQL_USER"),
    "password": os.getenv("MYSQL_PASSWORD"),
    "database": os.getenv("MYSQL_DATABASE"),
    "ssl_ca": os.getenv("MYSQL_SSL_CA")
}

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")

SEGMENTED_FOLDER_ID = os.getenv("SEGMENTED_FOLDER_ID")
FULL_FOLDER_ID = os.getenv("FULL_FOLDER_ID")

# === Qdrant Client ===
qdrant = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

# === Google Drive API Setup ===
SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE")
SCOPES = ["https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
drive_service = build("drive", "v3", credentials=creds)

# === Models ===
class SimilarityQuery(BaseModel):
    vector: List[float]
    top_k: int = 5
    filters: Optional[dict] = None

# === DB Helper ===
def get_db_connection():
    return mysql.connector.connect(**MYSQL_CONFIG)

# === Vector Dimension Handler ===
def pad_vector_to_512(vector):
    """Pad the input vector with zeros to reach 512 dimensions."""
    logger.info(f"Original vector length: {len(vector)}")
    if len(vector) < 512:
        padded_vector = vector + [0.0] * (512 - len(vector))
        logger.info(f"Padded vector to length: {len(padded_vector)}")
        return padded_vector
    return vector

# === 1. Recommendation Endpoints ===
from fastapi import Query
from fastapi import Body

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/metrics")
def metrics():
    """Prometheus metrics endpoint."""
    return PlainTextResponse(generate_latest(), media_type="text/plain; version=0.0.4; charset=utf-8")

@app.post("/matching")
def get_best_matching_image(
    gender: Optional[str] = Query(None),
    style: Optional[str] = Query(None),
    type_: Optional[str] = Query(None),
    vector: List[float] = Body(...)
):
    # Increment the matching request counter
    MATCHING_REQUESTS.inc()
    RECO_REQUESTS.inc()
    
    start_time = time.time()
    try:
        # Log vector information
        logger.info(f"Received vector of length: {len(vector)}")
        
        # Normalize gender input
        if gender:
            gender = gender.strip().lower()
            if gender == "male":
                gender = "MEN"
            elif gender == "female":
                gender = "WOMEN"

        # Determine opposite type
        if type_ == "topwear":
            opposite_type = "bottomwear"
        elif type_ == "bottomwear":
            opposite_type = "topwear"
        else:
            raise HTTPException(status_code=400, detail="type_ must be either 'topwear' or 'bottomwear'")

        # Get segmented_pic_ids of opposite type
        conn = get_db_connection()
        cursor = conn.cursor()

        query = "SELECT segmented_pic_id FROM segmented_images WHERE 1=1"
        params = []

        if gender:
            query += " AND gender = %s"
            params.append(gender)
        query += " AND type = %s"
        params.append(opposite_type)
        if style:
            query += " AND style = %s"
            params.append(style)

        cursor.execute(query, tuple(params))
        result = [row[0] for row in cursor.fetchall()]
        if not result:
            conn.close()
            raise HTTPException(status_code=404, detail="No matching segmented_pic_ids found.")

        # Qdrant color search
        filters = {"segmented_pic_ids": result}
        qdrant_filter = build_qdrant_filter(filters)
        
        # Pad vector to expected dimension
        padded_vector = pad_vector_to_512(vector)

        hits = qdrant.search(
            collection_name=COLLECTION_NAME,
            query_vector={"name": "color", "vector": padded_vector},
            query_filter=qdrant_filter,
            limit=1
        )

        if not hits:
            conn.close()
            raise HTTPException(status_code=404, detail="No match found in Qdrant.")

        top_id = hits[0].payload.get("segmented_pic_id")

        # Get full_image_id from DB
        cursor.execute("SELECT full_image_id FROM segmented_images WHERE segmented_pic_id = %s", (top_id,))
        full_image_row = cursor.fetchone()
        conn.close()
        if not full_image_row:
            raise HTTPException(status_code=404, detail="Full image ID not found.")
        full_image_id = full_image_row[0]

        # Download full image from Drive
        query_full = f"name = '{full_image_id}.jpg' and '{FULL_FOLDER_ID}' in parents"
        full_results = drive_service.files().list(q=query_full, spaces='drive', fields="files(id, name)").execute()
        full_files = full_results.get("files", [])
        if not full_files:
            raise HTTPException(status_code=404, detail="Full image not found in Drive")
        full_file_id = full_files[0]["id"]

        full_request = drive_service.files().get_media(fileId=full_file_id)
        full_fh = io.BytesIO()
        full_downloader = MediaIoBaseDownload(full_fh, full_request)
        done = False
        while not done:
            _, done = full_downloader.next_chunk()
        full_fh.seek(0)

        # Measure processing time
        processing_time = time.time() - start_time
        RECO_PROCESSING_TIME.observe(processing_time)
        
        return StreamingResponse(full_fh, media_type="image/jpeg")
    except Exception as e:
        # Increment error counter
        RECO_ERRORS.inc()
        
        logger.error(f"Error in get_best_matching_image: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/similarity")
def get_similar_full_image(
    gender: Optional[str] = Query(None),
    style: Optional[str] = Query(None),
    type_: Optional[str] = Query(None),
    vector: List[float] = Body(...)
):
    # Increment the similarity request counter
    SIMILARITY_REQUESTS.inc()
    RECO_REQUESTS.inc()
    
    start_time = time.time()
    try:
        # Log vector information
        logger.info(f"Received vector of length: {len(vector)}")
        
        # Normalize gender input
        if gender:
            gender = gender.strip().lower()
            if gender == "male":
                gender = "MEN"
            elif gender == "female":
                gender = "WOMEN"

        # Ensure valid type_
        if type_ not in ["topwear", "bottomwear"]:
            raise HTTPException(status_code=400, detail="type_ must be either 'topwear' or 'bottomwear'")

        # Step 1: Get segmented_pic_ids of the same type
        conn = get_db_connection()
        cursor = conn.cursor()

        query = "SELECT segmented_pic_id FROM segmented_images WHERE 1=1"
        params = []

        if gender:
            query += " AND gender = %s"
            params.append(gender)
        query += " AND type = %s"
        params.append(type_)
        if style:
            query += " AND style = %s"
            params.append(style)

        cursor.execute(query, tuple(params))
        result = [row[0] for row in cursor.fetchall()]
        if not result:
            conn.close()
            raise HTTPException(status_code=404, detail="No matching segmented_pic_ids found.")

        # Step 2: Qdrant feature vector search
        filters = {"segmented_pic_ids": result}
        qdrant_filter = build_qdrant_filter(filters)
        
        # Pad vector to expected dimension
        padded_vector = pad_vector_to_512(vector)

        hits = qdrant.search(
            collection_name=COLLECTION_NAME,
            query_vector={"name": "feature", "vector": padded_vector},
            query_filter=qdrant_filter,
            limit=1
        )

        if not hits:
            conn.close()
            raise HTTPException(status_code=404, detail="No match found in Qdrant.")

        top_id = hits[0].payload.get("segmented_pic_id")

        # Step 3: Get full_image_id from DB
        cursor.execute("SELECT full_image_id FROM segmented_images WHERE segmented_pic_id = %s", (top_id,))
        full_image_row = cursor.fetchone()
        conn.close()
        if not full_image_row:
            raise HTTPException(status_code=404, detail="Full image ID not found.")

        full_image_id = full_image_row[0]

        # Step 4: Download full image from Drive
        query_full = f"name = '{full_image_id}.jpg' and '{FULL_FOLDER_ID}' in parents"
        full_results = drive_service.files().list(q=query_full, spaces='drive', fields="files(id, name)").execute()
        full_files = full_results.get("files", [])
        if not full_files:
            raise HTTPException(status_code=404, detail="Full image not found in Drive")
        full_file_id = full_files[0]["id"]

        full_request = drive_service.files().get_media(fileId=full_file_id)
        full_fh = io.BytesIO()
        full_downloader = MediaIoBaseDownload(full_fh, full_request)
        done = False
        while not done:
            _, done = full_downloader.next_chunk()
        full_fh.seek(0)

        # Measure processing time
        processing_time = time.time() - start_time
        RECO_PROCESSING_TIME.observe(processing_time)
        
        return StreamingResponse(full_fh, media_type="image/jpeg")
    except Exception as e:
        # Increment error counter
        RECO_ERRORS.inc()
        
        logger.error(f"Error in get_similar_full_image: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/recommendation")
def recommendation_route(
    operation: str = Query(...),  # "matching" or "similarity"
    gender: Optional[str] = Query(None),
    style: Optional[str] = Query(None),
    type_: Optional[str] = Query(None),
    vector: List[float] = Body(...)
):
    # Increment the recommendation request counter
    RECO_REQUESTS.inc()
    
    start_time = time.time()
    try:
        logger.info(f"Recommendation request: {operation}, gender: {gender}, style: {style}, type: {type_}")
        logger.info(f"Vector length: {len(vector)}")
        
        # Pad vector to expected dimension
        padded_vector = pad_vector_to_512(vector)
        
        if operation == "matching":
            return get_best_matching_image(gender, style, type_, padded_vector)
        elif operation == "similarity":
            return get_similar_full_image(gender, style, type_, padded_vector)
        else:
            raise HTTPException(status_code=400, detail="Invalid operation. Must be 'matching' or 'similarity'")
    except HTTPException as he:
        # Pass through HTTP exceptions
        raise he
    except Exception as e:
        # Increment error counter
        RECO_ERRORS.inc()
        
        logger.error(f"Error in recommendation_route: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# === Entry point to run from terminal ===
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8007)

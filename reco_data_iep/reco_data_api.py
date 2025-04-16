from fastapi import FastAPI, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
import mysql.connector
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct, Filter, FieldCondition, MatchValue
import numpy as np
import io
from fastapi.responses import StreamingResponse
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2.service_account import Credentials
import uvicorn
from qdrant_client.http.models import MatchAny
from dotenv import load_dotenv
import os

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

# === 1. Recommendation Endpoints ===
from fastapi import Query
from fastapi import Body

@app.post("/matching")
def get_best_matching_image(
    gender: Optional[str] = Query(None),
    style: Optional[str] = Query(None),
    type_: Optional[str] = Query(None),
    vector: List[float] = Body(...)
):
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

    hits = qdrant.search(
        collection_name=COLLECTION_NAME,
        query_vector={"name": "color", "vector": vector},
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

    return StreamingResponse(full_fh, media_type="image/jpeg")

@app.post("/similarity")
def get_similar_full_image(
    gender: Optional[str] = Query(None),
    style: Optional[str] = Query(None),
    type_: Optional[str] = Query(None),
    vector: List[float] = Body(...)
):
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

    hits = qdrant.search(
        collection_name=COLLECTION_NAME,
        query_vector={"name": "feature", "vector": vector},
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

    return StreamingResponse(full_fh, media_type="image/jpeg")

@app.post("/recommendation")
def recommendation_route(
    operation: str = Query(...),  # "matching" or "similarity"
    gender: Optional[str] = Query(None),
    style: Optional[str] = Query(None),
    type_: Optional[str] = Query(None),
    vector: List[float] = Body(...)
):
    """
    Main recommendation endpoint that dispatches to either matching or similarity
    based on the operation parameter.
    
    Args:
        operation: Either "matching" or "similarity"
        gender: Optional gender filter (male/female)
        style: Optional style filter
        type_: Type of clothing ("topwear" or "bottomwear")
        vector: Feature vector for similarity, color histogram for matching
        
    Returns:
        StreamingResponse with JPEG image
    """
    if operation == "matching":
        return get_best_matching_image(gender, style, type_, vector)
    else:  # Assume similarity for any other value
        return get_similar_full_image(gender, style, type_, vector)

# === Entry point to run from terminal ===
if __name__ == "__main__":
    uvicorn.run("reco_data_api:app", host="0.0.0.0", port=8007, reload=True)

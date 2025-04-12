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
app = FastAPI(title="Data Access API", version="1.0")

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

# === 1. Filter IDs ===
from fastapi import Query

@app.get("/filter_ids")
def get_filtered_segmented_ids(
    gender: Optional[str] = Query(None),
    type_: Optional[str] = Query(None),
    style: Optional[str] = Query(None)
):
    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT segmented_pic_id FROM segmented_images WHERE 1=1"
    params = []

    if gender:
        query += " AND gender = %s"
        params.append(gender)
    if type_:
        query += " AND type = %s"
        params.append(type_)
    if style:
        query += " AND style = %s"
        params.append(style)

    cursor.execute(query, tuple(params))
    result = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return {"segmented_pic_ids": result}


# === 2. Get feature vector ===
@app.get("/feature_vector/{seg_id}")
def get_feature_vector(seg_id: str):
    result = qdrant.scroll(collection_name=COLLECTION_NAME, scroll_filter=Filter(must=[
        FieldCondition(key="segmented_pic_id", match=MatchValue(value=seg_id))]),
        with_vectors=True, limit=1)[0]
    if not result:
        raise HTTPException(status_code=404, detail="Feature vector not found")
    return result[0].vector["feature"]

# === 3. Get color vector ===
@app.get("/color_vector/{seg_id}")
def get_color_vector(seg_id: str):
    result = qdrant.scroll(collection_name=COLLECTION_NAME, scroll_filter=Filter(must=[
        FieldCondition(key="segmented_pic_id", match=MatchValue(value=seg_id))]),
        with_vectors=True, limit=1)[0]
    if not result:
        raise HTTPException(status_code=404, detail="Color vector not found")
    return result[0].vector["color"]

# === 4. Search by feature ===
@app.post("/search/feature")
def search_by_feature(q: SimilarityQuery):
    qdrant_filter = build_qdrant_filter(q.filters)
    hits = qdrant.search(
        collection_name=COLLECTION_NAME,
        query_vector={"name": "feature", "vector": q.vector},
        query_filter=qdrant_filter,
        limit=q.top_k
    )
    return [{"id": h.payload.get("segmented_pic_id"), "score": h.score} for h in hits]

# === 5. Search by color (euclidean) ===
@app.post("/search/color")
def search_by_color(q: SimilarityQuery):
    qdrant_filter = build_qdrant_filter(q.filters)
    hits = qdrant.search(
        collection_name=COLLECTION_NAME,
        query_vector={"name": "color", "vector": q.vector},
        query_filter=qdrant_filter,
        limit=q.top_k
    )
    return [{"id": h.payload.get("segmented_pic_id"), "score": h.score} for h in hits]

# === 6. Metadata from MySQL ===
@app.get("/metadata/{seg_id}")
def get_metadata(seg_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM segmented_images WHERE segmented_pic_id = %s", (seg_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="ID not found")
    return {
        "segmented_pic_id": row[0],
        "style": row[1],
        "gender": row[2],
        "type": row[3],
        "full_image_id": row[4]
    }

# === 7. Serve segmented image from Drive ===
@app.get("/image/segmented/{seg_id}")
def get_segmented_image(seg_id: str):
    query = f"name = '{seg_id}.jpg' and '{SEGMENTED_FOLDER_ID}' in parents"
    results = drive_service.files().list(q=query, spaces='drive', fields="files(id, name)").execute()
    files = results.get("files", [])
    if not files:
        raise HTTPException(status_code=404, detail="Image not found")
    file_id = files[0]["id"]
    request = drive_service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    fh.seek(0)
    return StreamingResponse(fh, media_type="image/jpeg")

# === 8. Serve full image from Drive ===
@app.get("/image/full/{full_image_id}")
def get_full_image(full_image_id: str):
    query = f"name = '{full_image_id}.jpg' and '{FULL_FOLDER_ID}' in parents"
    results = drive_service.files().list(q=query, spaces='drive', fields="files(id, name)").execute()
    files = results.get("files", [])
    if not files:
        raise HTTPException(status_code=404, detail="Full image not found")
    file_id = files[0]["id"]
    request = drive_service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    fh.seek(0)
    return StreamingResponse(fh, media_type="image/jpeg")

# === Entry point to run from terminal ===
if __name__ == "__main__":
    uvicorn.run("data_access_api:app", host="0.0.0.0", port=8007, reload=True)

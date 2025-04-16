
# 👗 Fashion Recommendation API (FastAPI + Qdrant + MySQL + Google Drive)

This project provides a RESTful API for fashion image recommendation and similarity search using:

- 🧠 Vector similarity with [Qdrant](https://qdrant.tech/)
- 🛍 MySQL for metadata
- ☁️ Google Drive for image storage
- ⚡ FastAPI as the backend
- 🐳 Dockerized for easy deployment

---

## 📦 Features

- **/matching**: Given a clothing item's color vector, find a complementary match (e.g. top → bottom).
- **/similarity**: Given a clothing item's feature vector, find a similar item (e.g. shirt → similar shirt).
- Streams back the **full original image** from Google Drive.

---

## 🧰 Requirements

- Docker & Docker Compose (optional)
- A `.env` file with credentials for:
  - MySQL database
  - Qdrant Cloud/API
  - Google Drive API (Service Account)

---

## ⚙️ Environment Variables (`.env`)

Create a `.env` file in your project root:

```env
MYSQL_HOST=your-mysql-host
MYSQL_PORT=3306
MYSQL_USER=username
MYSQL_PASSWORD=password
MYSQL_DATABASE=your_database
MYSQL_SSL_CA=/path/to/ssl.pem

QDRANT_URL=https://your-qdrant-cloud-url
QDRANT_API_KEY=your-qdrant-api-key
COLLECTION_NAME=fashion_features

SEGMENTED_FOLDER_ID=your_google_drive_folder_id_for_segmented
FULL_FOLDER_ID=your_google_drive_folder_id_for_full_images
SERVICE_ACCOUNT_FILE=google_creds.json
```

> ✅ Make sure your `SERVICE_ACCOUNT_FILE` is in the project directory.

---

## 🐳 Docker Setup

### 1. Build the Docker image

```bash
docker build -t reco-api .
```

### 2. Run the container on a custom port (e.g. 8010)

```bash
docker run -p 8010:8007 --env-file .env reco-api
```

Now access the API at: [http://localhost:8010](http://localhost:8010)

---

## 🔗 API Endpoints

### `POST /matching`

Finds a **matching item** of opposite type.

#### Params (Query)

- `gender`: `"male"` or `"female"` (optional)
- `style`: `"casual"`, `"formal"`, etc. (optional)
- `type_`: `"topwear"` or `"bottomwear"` (**required**)

#### Body

```json
{
  "vector": [0.25, 0.89, ...]  // Color vector
}
```

#### Response

Returns the matched image as a JPEG stream.

---

### `POST /similarity`

Finds a **similar item** (same type).

#### Params (Query)

- `gender`: `"male"` or `"female"` (optional)
- `style`: `"casual"`, `"formal"`, etc. (optional)
- `type_`: `"topwear"` or `"bottomwear"` (**required**)

#### Body

```json
{
  "vector": [0.25, 0.89, ...]  // Feature vector
}
```

#### Response

Returns the similar image as a JPEG stream.

---

## 🧪 Testing

After running:

```
docker run -p 8010:8007 --env-file .env reco-api
```

Test the API with:

```bash
curl -X POST "http://localhost:8010/matching?gender=male&type_=topwear" \
  -H "Content-Type: application/json" \
  -d '{"vector": [0.1, 0.2, 0.3, ...]}'
```

---

## 🧠 Future Ideas

- Add Swagger docs (`/docs`)
- Add virtual try-on integration
- Store processed logs in S3 or BigQuery
- Integrate with fashion e-commerce APIs

---

## 🧑‍💻 Author

Made with ❤️ by [Your Name].  
Feel free to contribute or suggest ideas!

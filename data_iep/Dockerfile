# 🐍 Use official Python image
FROM python:3.10-slim

# 📁 Set working directory
WORKDIR /app

# 🧾 Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 📦 Copy all project files
COPY . .

# 🔥 Expose port for FastAPI
EXPOSE 8007

# 🚀 Run the FastAPI app
CMD ["uvicorn", "data_access_api:app", "--host", "0.0.0.0", "--port", "8007"]

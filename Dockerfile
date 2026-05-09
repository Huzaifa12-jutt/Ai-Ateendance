# Step 1: Python base image
FROM python:3.10-slim

# Step 2: Install system dependencies for Face Recognition & OpenCV
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Step 3: Set working directory
WORKDIR /app

# Step 4: Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Step 5: Copy all project files
COPY . .

# Step 6: Start the app with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:$PORT", "app:app"]
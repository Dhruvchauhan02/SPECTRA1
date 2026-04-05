FROM python:3.10-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    g++ \
    gcc \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
        torch==2.1.0+cpu \
        torchvision==0.16.0+cpu \
        --index-url https://download.pytorch.org/whl/cpu && \
    grep -vE "^torch|^torchvision|^streamlit" requirements.txt > req_filtered.txt && \
    pip install --no-cache-dir -r req_filtered.txt

COPY . .

# Ensure ai_models is a proper Python package
RUN mkdir -p ai_models/deepfake_detection \
    ai_models/face_recognition \
    ai_models/fake_news_detection && \
    touch ai_models/__init__.py && \
    touch ai_models/deepfake_detection/__init__.py && \
    touch ai_models/face_recognition/__init__.py && \
    touch ai_models/fake_news_detection/__init__.py && \
    mkdir -p uploads models logs

# Add /app to Python path so all modules resolve correctly
ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "api.main1:app", "--host", "0.0.0.0", "--port", "8000"]
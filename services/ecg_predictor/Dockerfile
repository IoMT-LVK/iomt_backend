FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y gcc python3-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

VOLUME /app/credentials

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
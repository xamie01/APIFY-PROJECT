FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc g++ git curl && \
    rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 -s /bin/bash osate && \
    chown -R osate:osate /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY --chown=osate:osate . .

RUN mkdir -p .actor

USER osate

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Apify actor entry point
CMD ["python", "-m", "src"]

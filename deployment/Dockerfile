FROM python:3.13-slim

LABEL maintainer="Varynx Platform Team"
LABEL description="Varynx autonomous-agent security platform"
LABEL version="1.0"

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements-platform.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements-platform.txt

COPY app ./app
COPY api ./api

ENV VARYNX_HOST=0.0.0.0
ENV VARYNX_PORT=8000
ENV VARYNX_ENVIRONMENT=container

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"

CMD ["uvicorn", "api.gateway:app", "--host", "0.0.0.0", "--port", "8000"]
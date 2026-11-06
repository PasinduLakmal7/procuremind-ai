FROM python:3.12-slim

WORKDIR /workspace

COPY shared/ /workspace/shared/

WORKDIR /workspace/workers/document-worker
COPY workers/document-worker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -e /workspace/shared

COPY workers/document-worker/ .

ENV PYTHONPATH=/workspace:/workspace/workers/document-worker

CMD ["celery", "-A", "worker.celery_app", "worker", "--loglevel=info"]

FROM python:3.12-slim

WORKDIR /workspace

COPY shared/ /workspace/shared/

WORKDIR /workspace/services/supplier-service
COPY services/supplier-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -e /workspace/shared

COPY services/supplier-service/ .

ENV PYTHONPATH=/workspace:/workspace/services/supplier-service
EXPOSE 8003

HEALTHCHECK --interval=15s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8003/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003"]

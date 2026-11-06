FROM python:3.12-slim

WORKDIR /workspace

# Copy shared foundation package first
COPY shared/ /workspace/shared/

# Copy service dependencies and code
WORKDIR /workspace/services/identity-service
COPY services/identity-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -e /workspace/shared

COPY services/identity-service/ .

ENV PYTHONPATH=/workspace:/workspace/services/identity-service
EXPOSE 8001

HEALTHCHECK --interval=15s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]

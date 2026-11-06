FROM python:3.12-slim

WORKDIR /workspace

COPY shared/ /workspace/shared/

WORKDIR /workspace/services/procurement-service
COPY services/procurement-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -e /workspace/shared

COPY services/procurement-service/ .

ENV PYTHONPATH=/workspace:/workspace/services/procurement-service
EXPOSE 8002

HEALTHCHECK --interval=15s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8002/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]

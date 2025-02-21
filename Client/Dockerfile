FROM python:3.9-slim
WORKDIR /app
COPY Requirements.txt .
COPY performance_metrics.py .
RUN pip install -r Requirements.txt
COPY client.py .
CMD ["python", "client.py"]
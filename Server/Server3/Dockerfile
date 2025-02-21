FROM python:3.9-slim
WORKDIR /app
COPY Requirements.txt .
RUN pip install -r Requirements.txt
COPY server.py .
CMD ["python", "server.py"]
FROM registry.linuxone.cloud.marist.edu/l1cc/jupyterlab-image-s390x:latest

WORKDIR /app

COPY . /app

RUN python3 -m pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH=/app

CMD ["python3", "-m", "uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"]
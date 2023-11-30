FROM python:3-alpine3.10

WORKDIR /app

COPY ../requirements.txt .
RUN pip install -f requirements.txt

ENTRYPOINT ["python3", "app.py"]
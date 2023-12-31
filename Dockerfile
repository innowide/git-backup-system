FROM python:3.11-alpine
COPY src/* .
RUN pip install --upgrade pip; pip install --no-cache-dir -r requirements.txt
RUN apk add git
VOLUME "/repos-backup"
CMD ["python", "main.py"]
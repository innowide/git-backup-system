FROM python:3.11-slim-buster
COPY src/ .
RUN pip install --upgrade pip; pip install --no-cache-dir -r requirements.txt
CMD ["python", "./main.py"]
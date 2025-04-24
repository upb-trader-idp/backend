FROM python:3.12-alpine

WORKDIR /app

COPY . .

ENV PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]
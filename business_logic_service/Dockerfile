FROM python:3.12-alpine

WORKDIR /app

COPY ./business_logic_service .

COPY ./shared ./shared

ENV PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]
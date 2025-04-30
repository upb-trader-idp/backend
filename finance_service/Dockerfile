FROM python:3.12-alpine

WORKDIR /app

COPY ./finance_service .

COPY ./shared ./shared

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8004

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8004"]

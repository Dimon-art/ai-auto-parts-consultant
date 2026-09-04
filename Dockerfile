FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/data && ln -sfn /app/data/parts_catalogs.db /app/parts_catalogs.db

EXPOSE 8023

CMD ["uvicorn", "web_app:app", "--host", "0.0.0.0", "--port", "8023"]
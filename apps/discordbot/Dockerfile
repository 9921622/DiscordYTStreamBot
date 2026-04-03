FROM python:3.12-slim AS base
WORKDIR /app
COPY requirements.txt .

FROM base AS development
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8080
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]

FROM base AS production
RUN pip install --no-cache-dir -r requirements-production.txt
COPY . .
EXPOSE 8080
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "2"]

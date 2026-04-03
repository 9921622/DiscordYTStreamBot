FROM python:3.12-slim AS base
WORKDIR /app
COPY requirements.txt .

FROM base AS development
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "src/manage.py", "runserver", "0.0.0.0:8000"]

FROM base AS production
RUN pip install --no-cache-dir -r requirements-production.txt
COPY . .
EXPOSE 8000
CMD ["gunicorn", "src.backend.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]

FROM python:3.12-slim AS base
WORKDIR /app
COPY requirements.txt requirements-production.txt ./

FROM base AS development
RUN pip install --no-cache-dir -r requirements.txt
# COPY . .  # mount from dev.
ENV PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["sh", "-c", "python src/manage.py migrate && \
                python src/manage.py runserver 0.0.0.0:8000"]

FROM base AS production
RUN pip install --no-cache-dir -r requirements-production.txt
COPY . .
EXPOSE 8000
ENV PYTHONPATH=/app/src
CMD ["sh", "-c", "python src/manage.py migrate && \
                gunicorn backend.wsgi:application --bind 0.0.0.0:8000 --workers 3"]

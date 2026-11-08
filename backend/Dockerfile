FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

RUN useradd --create-home appuser
USER appuser

EXPOSE 8000

# Apply migrations, optionally load the synthetic demo workforce, then serve
CMD ["sh", "-c", "alembic upgrade head && if [ \"$SEED_DEMO_DATA\" = \"true\" ]; then python -m app.scripts.seed_demo_data; fi && uvicorn app.main:app --host 0.0.0.0 --port 8000"]

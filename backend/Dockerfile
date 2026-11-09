FROM python:3.11-slim
WORKDIR /app
COPY backend/pyproject.toml .
RUN pip install --no-cache-dir -e .[dev] 2>/dev/null || pip install --no-cache-dir fastapi uvicorn pydantic pydantic-settings sqlalchemy networkx numpy pyyaml python-multipart httpx anthropic
COPY backend/ ./backend/
ENV DATABASE_URL=sqlite:////app/jarvis.db
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--app-dir", "backend"]

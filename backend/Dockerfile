FROM python:3.12-slim AS base

FROM base AS builder

WORKDIR /app

COPY requirements.txt .
RUN python -m venv /opt/venv
RUN . /app/venv/bin/activate &&pip install --no-cache-dir -r requirements.txt

FROM base AS runner

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

ENV PATH="/opt/venv/bin:$PATH"

ENTRYPOINT [ ".", "/app/venv/bin/activate" ]

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

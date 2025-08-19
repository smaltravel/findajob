FROM python:3.12-slim AS base

FROM base AS builder

WORKDIR /app

COPY requirements.txt .
COPY entrypoint.sh .
RUN python -m venv /app/venv
RUN . /app/venv/bin/activate && pip install --no-cache-dir -r requirements.txt
RUN chmod +x entrypoint.sh

FROM base AS runner

WORKDIR /app

COPY --from=builder /app/venv /app/venv
COPY --from=builder /app/entrypoint.sh /app/entrypoint.sh

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

ENV PATH="/app/venv/bin:$PATH"

ENTRYPOINT [ "./entrypoint.sh" ]

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

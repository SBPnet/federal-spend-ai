FROM python:3.11-slim-bookworm

WORKDIR /app

# Build tools for wheels that may not have prebuilt binaries on slim images.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md LICENSE ./
COPY src ./src
COPY tests/fixtures ./tests/fixtures

RUN pip install --no-cache-dir -e . \
    && python -m spacy download en_core_web_sm

ENV FEDERALSPEND_DATA_DIR=/data
VOLUME ["/data"]

# SSE transport exposes HTTP for remote MCP clients.
EXPOSE 8000

ENV FEDERALSPEND_ENGINE_ENABLED=true
ENV FEDERALSPEND_ENGINE_DATASETS=awards,public_accounts
ENV FEDERALSPEND_ENGINE_POLL_INTERVAL_SECONDS=3600
ENV FEDERALSPEND_ENGINE_RUN_ON_START=true

CMD ["federalspendai", "engine", "--transport", "sse", "--port", "8000"]

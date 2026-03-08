FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /srv/policier

# Build from repo root:
# docker build -f app/templates/agent/policier/Dockerfile -t policier:latest .
COPY app/templates/agent/policier/pyproject.toml ./
RUN uv sync --no-dev

COPY app/templates/agent/policier/ ./

# Mount your repo to /workspace when running the container.
ENV POLICY_BASE_DIR=/workspace

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]

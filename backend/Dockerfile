# Base image: slim variant keeps the image small — no build tools, no extras.
# Pinned to 3.12 to match pyproject.toml's requires-python constraint.
FROM python:3.12-slim

# PYTHONUNBUFFERED: forces stdout/stderr to flush immediately.
# Without this, logs are buffered and you see nothing in Cloud Run until the
# buffer fills — makes debugging painful.
ENV PYTHONUNBUFFERED=1

# PYTHONDONTWRITEBYTECODE: stops Python writing .pyc files to disk.
# In a container the source files are already there — compiled bytecache
# just adds noise and wastes space.
ENV PYTHONDONTWRITEBYTECODE=1

# Copy the uv binary directly from the official uv image.
# This avoids the pip → uv bootstrap impurity (pip install uv).
# The uv binary is statically linked, so it runs with no extra dependencies.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy dependency manifests before application code.
# Docker builds layers sequentially and caches each one. By copying only
# pyproject.toml and uv.lock first, we ensure that the expensive uv sync
# step is only re-run when dependencies actually change — not on every
# code change. This makes iterative rebuilds fast.
COPY pyproject.toml uv.lock ./

# Install production dependencies from the lockfile.
# --frozen: use exactly the versions in uv.lock, no re-resolution.
# --no-dev: exclude dev dependency groups (pytest, ruff, mypy, etc.).
#           These have no place in a production image.
RUN uv sync --frozen --no-dev

# Copy the rest of the application code.
# Comes after uv sync so that code-only changes don't bust the dep cache.
COPY . .

# Create a non-root user and transfer ownership of /app to it.
# Defence-in-depth: if the process is ever compromised, it cannot modify
# system files or escape to root-owned paths.
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Document the port the app listens on. Cloud Run reads this as a hint,
# but the actual binding is controlled by the CMD below.
EXPOSE 8000

# Cloud Run injects a PORT environment variable at runtime pointing to the
# port it expects the container to listen on. We honour it and fall back
# to 8000 for local docker run usage. --host 0.0.0.0 is required in a
# container — 127.0.0.1 would make the process unreachable from outside.
#
# We call uvicorn directly from the venv rather than via `uv run`.
# `uv run` checks whether the venv is up to date and re-syncs if not —
# at container startup that means downloading packages, wasting time and
# memory before the app even starts. The venv was built correctly at image
# build time and doesn't need re-checking at runtime.
CMD ["sh", "-c", ".venv/bin/uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]

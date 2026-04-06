# Agent Context — Story Engine

## Singletons

Expensive clients and services that are safe to share across requests are instantiated once using `@lru_cache(maxsize=1)` on a named factory function. Do not instantiate them inline.

- `get_gcs_upload_service()` — returns the process-wide `GCSUploadService` instance (GCS client + connection pool)
- `fal_async_client` — module-level singleton in `core/services/intelligence/media_generator.py`; uses an internal semaphore to gate concurrent fal requests

When adding new shared infrastructure, follow the `get_gcs_upload_service()` pattern: factory function with `@lru_cache(maxsize=1)`, clearly named as a getter.

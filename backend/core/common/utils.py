from datetime import datetime, timezone


def get_current_timestamp_seconds() -> int:
    return int(datetime.now(timezone.utc).timestamp())


def get_current_timestamp_ms() -> int:
    return int(datetime.now(timezone.utc).timestamp() * 1000)


def get_current_datetime_utc() -> datetime:
    return datetime.now(timezone.utc)

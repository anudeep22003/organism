from datetime import datetime, timezone


def get_current_timestamp_seconds() -> int:
    return int(datetime.now(timezone.utc).timestamp())

from datetime import datetime, timedelta


def get_current_time() -> datetime:
    return datetime.utcnow()


def add_hours(hours: int) -> datetime:
    return get_current_time() + timedelta(hours=hours)

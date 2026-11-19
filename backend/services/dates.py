"""Small date helpers so "today" means the same thing everywhere."""
from datetime import date, datetime, timezone


def today() -> date:
    """Today's date on the machine running the server."""
    return date.today()


def to_local_date(value) -> date:
    """
    Database timestamps are saved in UTC (SQLite returns them without a
    timezone). This converts one to a calendar date in local time, so a
    quiz taken at 1 AM counts for that day and not the day before.
    """
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone().date()
    return value

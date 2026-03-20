from __future__ import annotations

from collections.abc import Iterator
from datetime import date, datetime, time, timedelta
from random import Random


def date_sequence(start_date: date, end_date: date) -> Iterator[date]:
    current_date = start_date
    while current_date <= end_date:
        yield current_date
        current_date += timedelta(days=1)


def random_timestamp(current_date: date, start_hour: int, end_hour: int, rng: Random) -> datetime:
    if start_hour <= end_hour:
        hour = rng.randint(start_hour, end_hour)
    else:
        possible_hours = list(range(start_hour, 24)) + list(range(0, end_hour + 1))
        hour = rng.choice(possible_hours)

    minute = rng.randint(0, 59)
    second = rng.randint(0, 59)
    return datetime.combine(current_date, time(hour=hour, minute=minute, second=second))

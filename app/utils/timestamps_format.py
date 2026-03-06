from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

def timestamps_format(
  start_date: Optional[datetime],
  end_date: Optional[datetime] 
) -> Tuple[datetime, datetime]:
  # Якщо користувач не передав дати — беремо поточний тиждень
  if start_date is None or end_date is None:
    now = datetime.now(timezone.utc)
    start_of_week = (now - timedelta(days=now.weekday())).replace(
      hour=0, minute=0, second=0, microsecond=0
    )
    end_of_week = start_of_week + timedelta(days=7)
    start_date = start_of_week
    end_date = end_of_week
  # Перетворюємо на naive datetime для сумісності з БД (TIMESTAMP WITHOUT TIME ZONE)
  start_date = start_date.replace(tzinfo=None)
  end_date = end_date.replace(tzinfo=None)
  return start_date, end_date

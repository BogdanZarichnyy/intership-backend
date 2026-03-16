from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

def normalize_timestamps(
  start_date: Optional[datetime],
  end_date: Optional[datetime] 
) -> Tuple[datetime, datetime]:
  now = datetime.now(timezone.utc)
  # якщо обидві дати не передані → беремо поточний тиждень
  if start_date is None and end_date is None:
    # поточний тиждень
    start_date = now - timedelta(days=now.weekday())
    start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = start_date + timedelta(days=7)
  elif start_date and end_date is None:
    # якщо передано тільки start_date
    end_date = now
  elif end_date and start_date is None:
    # якщо передано тільки end_date
    start_date = end_date - timedelta(days=7)
  # Перетворюємо на naive datetime для сумісності з БД (TIMESTAMP WITHOUT TIME ZONE)
  return start_date.replace(tzinfo=None), end_date.replace(tzinfo=None)

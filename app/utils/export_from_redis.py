import csv
import io
import json
from typing import Any, List, Dict

def generate_json(data: Any, indent: int = 2) -> str:
  return json.dumps(data, ensure_ascii=False, indent=indent)

def generate_csv(rows: List[Dict]) -> io.StringIO:
  if not rows:
    return io.StringIO()  # Порожній файл
  buffer = io.StringIO()
  writer = csv.DictWriter(buffer, fieldnames=list(rows[0].keys()))
  writer.writeheader()
  writer.writerows(rows)
  buffer.seek(0)
  return buffer

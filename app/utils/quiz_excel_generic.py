import pandas as pd
from io import BytesIO
from typing import Dict, Any

def json_to_excel_file(
  json_data: Dict[str, Any]
) -> BytesIO:
  """
  Перетворює JSON квізу у Excel у форматі, який розбирає parse_quiz_excel.
  Повертає BytesIO, щоб його можна було передати як file= у import_excel.
  """
  rows = []

  for question in json_data.get("questions", []):
    for option in question.get("options", []):
      rows.append({
        "quiz_title": json_data.get("title"),
        "description": json_data.get("description"),
        "question": question.get("title"),
        "allows_multiple": question.get("allows_multiple_correct", False),
        "option_text": option.get("text"),
        "is_correct": option.get("is_correct", False)
      })

  df = pd.DataFrame(rows)
  output = BytesIO()
  df.to_excel(output, index=False)
  output.seek(0)  # Повертаємо курсор на початок
  return output

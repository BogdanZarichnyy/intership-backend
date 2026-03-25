import pandas as pd
from typing import List, Dict, Any, IO

def parse_quiz_excel(file: IO) -> List[Dict[str, Any]]:
  df = pd.read_excel(file)

  quizzes = {}

  for _, row in df.iterrows():
    title = row["title"]

    if title not in quizzes:
      quizzes[title] = {
        "title": title,
        "description": row.get("description"),
        "questions": {}
      }

    q_title = row["question"]

    if q_title not in quizzes[title]["questions"]:
      quizzes[title]["questions"][q_title] = {
        "title": q_title,
        "allows_multiple_correct": bool(row["allows_multiple_correct"]),
        "options": []
      }

    quizzes[title]["questions"][q_title]["options"].append({
      "text": row["option"],
      "is_correct": bool(row["is_correct"])
    })

  result = []
  for quiz in quizzes.values():
    quiz["questions"] = list(quiz["questions"].values())
    result.append(quiz)

  return result

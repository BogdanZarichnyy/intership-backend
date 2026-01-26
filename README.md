# intership-backend
intership-backend

Ініціалізація залежностей із папки .venv для проекту:
  pip freeze > requirements.txt
Встановлення залежностей із файлу requirements.txt для проекту:
  pip install -r requirements.txt

Запуск бекенда:
  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

Для тестів потрібна бібліотека httpx
  pip install httpx
  pip show httpx

Команда для запуску тестів для Windows:
  PYTHONPATH=. pytest tests/

  альтернативні варіанти запустку тестів для UNIX систем:
    pytest --rootdir=. tests/
    pytest tests/
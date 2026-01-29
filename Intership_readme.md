# intership-backend
intership-backend

У Windows + Bash:

  Інструмент	❌ НЕ ТАК	✅ ПРАВИЛЬНО
  pytest	    pytest	    python -m pytest
  uvicorn	    uvicorn	    python -m uvicorn
  pip	        pip	        python -m pip

  (де python = .venv/Scripts/python)

Ініціалізація залежностей із папки .venv для проекту:
  pip freeze > requirements.txt
Встановлення залежностей із файлу requirements.txt для проекту:
  pip install -r requirements.txt

При проблемах із запуском серверу потрібно ввести наступні команди:
  source .venv/Scripts/activate
  (.venv) - має показати це

  which python
  /d/github_projects/intership-backend/.venv/Scripts/python
  (.venv) - має показати це

Запуск бекенда:
  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
Якщо не спрацює, то запускати напряму: 
  python -m uvicorn app.main:app --reload

Для тестів потрібна бібліотека httpx
  pip install httpx
  pip show httpx

Команда для запуску тестів для Windows:
  PYTHONPATH=. .venv/Scripts/python -m pytest tests/

  альтернативні варіанти запустку тестів для UNIX систем:
    pytest --rootdir=. tests/
    pytest tests/
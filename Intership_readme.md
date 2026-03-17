# intership-backend

ТЗ: https://flash-people-437.notion.site/Tasks-Back-End-15-eng-version-2bca27416b388197bf4bf195775eaf30#2bca27416b388118b66cca861cdeec57
Backend-сервіс, побудований за допомогою **FastAPI**
Endpoints маршрути: http://localhost:8000/docs

## ⚠️ Windows, VSCode + Bash:

| Інструмент | ❌ НЕ ТАК | ✅ ПРАВИЛЬНО       |
|------------|------------|--------------------|
| pytest	   |`pytest`	  |`python -m pytest`  |
| uvicorn    |`uvicorn`	  |`python -m uvicorn` |
| pip	       |`pip`	      |`python -m pip`     |

> Де `python` стосується:
>
> ```bash
> .venv/Scripts/python
> ```

## 📦 Менеджер залежностей

Ініціалізація залежностей із папки .venv для проекту:
  ```bash
  pip freeze > requirements.txt
  ```
Встановлення залежностей із файлу requirements.txt для проекту:
  ```bash
  pip install -r requirements.txt
  ```

При проблемах із запуском серверу потрібно ввести наступні команди (для Windows):
  ```bash
  "/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe" -m venv .venv
  ```

## 🐍 Активація віртуального середовища (Windows + Bash)

Активація середовища:
  ```bash
  python -m venv venv
  source venv/Scripts/activate
  ```
  Результат:
    ```bash
    (.venv)
    ```

Перевірка середовища запуску:
  ```bash
  which python
  ```
  Результат:
    ```bash
    /d/github_projects/intership-backend/.venv/Scripts/python
    (.venv)
    ```

## Встановлення dotenv для приватних змінних
  ```bash
  python -m pip install python-dotenv
  ```

Якщо будуть помилки при запуску то потрібно повторно активувати середовище і перевстановити dotenv:
  ```bash
  pip install --upgrade pip
  source venv/Scripts/activate
  python -m pip install --force-reinstall python-dotenv
  python.exe -m pip install --upgrade pip
  ```

Перевіряєм середовище запуску:
  ```bash
  python -c "import dotenv; print(dotenv.__file__)"
  ```
Результат має вигладати так:
  ```bash
  ...\intership-backend\venv\Lib\site-packages\dotenv\__init__.py
  ```

## 🚀 Запуск backend сервера

Альтернативний спосіб запуску сервера для Windows:
  ```bash
  "C:\Users\admin\AppData\Local\Programs\Python\Python314\python.exe" app/main.py
  ```

Встановлення uvicorn для перезапуску сервера при внесення змін в код:
  ```bash
  python -m pip install fastapi uvicorn
  ```

Запуск бекенда якщо uvicorn прописаний у main.py, він запускається як модуль, а не як файл:
  ```bash
  python -m app.main
  uvicorn app.main:app --reload
  ```

Альтернативний спосіб запуску якщо uvicorn не прописаний у main.py:
  ```bash
  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
  ```

Якщо не спрацює, то можна запустити напряму, але бажано все прописувати у main.py:
  ```bash
  python -m uvicorn app.main:app --reload
  ```

## 🧪 Тестування

Для тестів потрібна бібліотека httpx
  ```bash
  pip install httpx
  pip show httpx
  ```

Команда для запуску тестів для Windows:
  ```bash
  PYTHONPATH=. .venv/Scripts/python -m pytest --disable-warnings
  PYTHONPATH=. .venv/Scripts/python -m pytest tests/
  PYTHONPATH=. pytest tests/
  ```

Альтернативні варіанти запустку тестів для UNIX систем:
  ```bash
  python -m pytest tests/
  python -m pytest -v
  pytest --rootdir=. tests/
  pytest tests/
  ```

Запуск тестів в середині контейнера докера:
  спочатку в терміналі докера вводимо:
  ```bash
  cd /d/github_projects/intership-backend
  docker compose exec backend /bin/sh
  docker compose exec backend /bin/bash
  ```
  таким чином активується shell бекенду, і тоді запускаємо тести:
  ```bash
  pytest tests/
  ```
  для Windows
  ```bash
  cd "D:\github_projects\intership-backend"
  docker compose exec backend sh -c "export PYTHONPATH=/app && pytest tests/"
  ```

## 🧪 Конфігурація Docker

Збираємо контейнер docker:
  ```bash
  docker build --no-cache -t internship-backend .
  ```

Запускаємо контейнер docker:
  ```bash
  docker run -d -p 8000:8000 internship-backend
  ```
Якщо додлаємо нову бібліотеку чи сервіс в проект, потрібно оновити всі залежності:
  ```bash
  pip freeze > requirements.txt
  pip install -r requirements.txt
  ```

І знову зібрати контейнер наново без кешу:
  ```bash
  docker build --no-cache -t internship-backend .
  ```

Збірка з docker compose:
  ```bash
  docker compose up --build
  ```

А коли Docker "глючить":
  ```bash
  docker compose build --no-cache
  ```

Запус терміналу контейнера в Docker:
  ```bash
  docker ps
  docker exec -it [ID_CONTAINER] sh
  ```

Запус композера Docker:
  ```bash
  docker compose down -v
  docker compose build --no-cache
  docker compose up
  ```

  ```bash
  docker compose build --no-cache && docker compose up
  ```

Після внесення змін у код бекенду, можна перезбирати/перезапускати його окремо без перезапуску образів баз даних:
  ```bash
  docker compose up --build
  ```

## Запуск міграцій:
  ```bash
  uvicorn app.main:app --reload  # зупинений бекенд
  python -m alembic revision --autogenerate -m "create users table"  # створення міграції
  python -m alembic revision --autogenerate -m "create company table"  # створення міграції
  python -m alembic revision --autogenerate -m "create company actions tables"  # створення міграції
  python -m alembic revision --autogenerate -m "add roles for members"  # створення міграції
  python -m alembic revision --autogenerate -m "create quizzes table"  # створення міграції
  python -m alembic revision --autogenerate -m "create quiz workflow table"  # створення міграції
  python -m alembic revision --autogenerate -m "create indexes for analytics"  # створення міграції
  python -m alembic upgrade head  # запис міграції в БД для Windows
  alembic upgrade head  # запис міграції в БД для UNIX
  alembic -x db_url=postgresql+asyncpg://postgres:postgres@localhost:5433/internship_test_db upgrade head # для тестової БД
  SELECT typname FROM pg_type WHERE typtype = 'e'; # подивитись всі enum типи
  DROP TYPE invitationstatus;  # видалення старих/недійсних enum типів, "invitationstatus" назва enum типу
  uvicorn app.main:app --reload  # старт бекенду
  ```

## Структура папок проекту:
  ```bash
  tree /F /A > structure.txt
  source venv/Scripts/activate
  python -m app.main
  ```

 ## Первірка підключення до Redis в контейнері docker:
  Спочатку отримуємо список активних контейнерів і run_id того контейнера, який потрібно перевірити:
  ```bash
  docker ps
  docker exec -it redis redis-cli INFO server | grep run_id
  ```
  Має показати run_id по назві контейнера redis:
  ```bash
  admin@ASUS_RAMPAGE MINGW64 ~
  $ docker exec -it redis redis-cli INFO server | grep run_id
  run_id:19f681259eff15e8c6b7a9a52ec2bf90b8cec939
  ```
  Отримуємо run_id і порівнюємо з конфігурацією Redis в розширенні VSCode Redis Explorer - вони мають збігатися

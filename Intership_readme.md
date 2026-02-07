# intership-backend

Backend-сервіс, побудований за допомогою **FastAPI**

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
  /C/Users/admin/AppData/Local/Programs/Python/Python314/python.exe -m venv venv
  ```

## 🐍 Активація віртуального середовища (Windows + Bash)

Активація середовища:
  ```bash
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
  source venv\Scripts\activate
  python -m pip install --force-reinstall python-dotenv
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
  PYTHONPATH=. .venv/Scripts/python -m pytest tests/
  ```

Альтернативні варіанти запустку тестів для UNIX систем:
  ```bash
  pytest --rootdir=. tests/
  pytest tests/
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

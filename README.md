# intership-backend

Backend service built with **FastAPI**

## ⚠️ Windows, VSCode + Bash:

| Tool | ❌ NOT THIS | ✅ CORRECTLY |
|------------|------------|--------------------|
| pytest	   |`pytest`	  |`python -m pytest`  |
| uvicorn    |`uvicorn`	  |`python -m uvicorn` |
| pip	       |`pip`	      |`python -m pip`     |

> Where `python` refers to:
>
> ```bash
> .venv/Scripts/python
> ```

## 📦 Dependency Manager

### Save dependencies from .venv to requirements.txt:
  ```bash
  pip freeze > requirements.txt
  ```

### Install dependencies from requirements.txt:
  ```bash
  pip install -r requirements.txt
  ```

### Troubleshooting server startup issues (Windows):

If you have problems running the server, enter the following commands:
  ```bash
  /c/Users/admin/AppData/Local/Programs/Python/Python314/python.exe -m venv .venv
  ```

## 🐍 Virtual Environment Activation (Windows + Bash)

### Activate the environment:
  ```bash
  source .venv/Scripts/activate
  ```
  
  Result:
    ```bash
    (.venv)
    ```

### Verify the Python environment:
  ```bash
  which python
  ```
  
  Result:
    ```bash
    /d/github_projects/intership-backend/.venv/Scripts/python
    (.venv)
    ```

## 🚀 Run Backend Server

### Alternative way to run the server on Windows:
  ```bash
  "C:\Users\admin\AppData\Local\Programs\Python\Python314\python.exe" app/main.py
  ```

### Install `uvicorn` to restart the server when code changes:
  ```bash
  python -m pip install fastapi uvicorn
  ```

### Run the backend if `uvicorn` is configured in `main.py` (module mode, not as a file):
  ```bash
  python -m app.main
  ```

### Alternative - If `uvicorn` is NOT configured in `main.py`:
  ```bash
  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
  ```

If that doesn't work, you can run it directly, but it's recommended to configure it in `main.py`:
  ```bash
  python -m uvicorn app.main:app --reload
  ```

## 🧪 Testing

Tests require the **httpx** library:
  ```bash
  pip install httpx
  pip show httpx
  ```

Command to run tests on Windows:
  ```bash
  PYTHONPATH=. .venv/Scripts/python -m pytest tests/
  ```

Alternative test commands for UNIX-like systems:
  ```bash
  pytest --rootdir=. tests/
  pytest tests/
  ```

## 🧪 Docker Configuration

Build the Docker container:
  ```bash
  docker build --no-cache -t internship-backend .
  ```

Run the Docker container:
  ```bash
  docker run -d -p 8000:8000 internship-backend
  ```

If you add a new library or service to the project, update all dependencies:
  ```bash
  pip freeze > requirements.txt
  pip install -r requirements.txt
  ```

Then rebuild the container without cache:
  ```bash
  docker build --no-cache -t internship-backend .
  ```

Build with Docker Compose:
  ```bash
  docker compose up --build
  ```

If Docker malfunctions:
  ```bash
  docker compose build --no-cache
  ```

Open a shell in the Docker container:
  ```bash
  docker ps
  docker exec -it [ID_CONTAINER] sh
  ```

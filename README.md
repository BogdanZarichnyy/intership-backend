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

### Alternative way to run the server (Windows):
  ```bash
  "C:\Users\admin\AppData\Local\Programs\Python\Python314\python.exe" app/main.py
  ```

### Install FastAPI and uvicorn for server restart on code changes:
  ```bash
  python -m pip install fastapi uvicorn
  ```

### Run the backend if uvicorn is configured in main.py (run as a module, not as a file):
  ```bash
  python -m app.main
  ```

### Alternative 1 - If uvicorn is NOT configured in main.py:
  ```bash
  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
  ```

### Alternative 2 - Direct uvicorn run (less preferred):

If the above doesn't work, you can run it directly, but it's better to configure it in main.py:
  ```bash
  python -m uvicorn app.main:app --reload
  ```

## 🧪 Testing

### Install required dependency:

Tests require the **httpx** library:
  ```bash
  pip install httpx
  pip show httpx
  ```

### Run tests (Windows):
  ```bash
  PYTHONPATH=. .venv/Scripts/python -m pytest tests/
  ```

### Alternative methods (Unix-like systems):
  ```bash
  pytest --rootdir=. tests/
  pytest tests/
  ```

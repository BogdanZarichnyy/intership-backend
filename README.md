# intership-backend

Backend service built with **FastAPI**.

---

## ⚠️ Important note for Windows + Bash users

On **Windows when using Bash (Git Bash / VS Code Bash)**, global executables may not work as expected. Always prefer running tools via Python.

| Tool    | ❌ Incorrect | ✅ Correct |
|--------|-------------|-----------|
| pytest | `pytest`    | `python -m pytest` |
| uvicorn | `uvicorn` | `python -m uvicorn` |
| pip    | `pip`       | `python -m pip` |

> Where `python` refers to:
>
> ```bash
> .venv/Scripts/python
> ```

---

## 📦 Dependency management

### Save dependencies

```bash
python -m pip freeze > requirements.txt
```

### Install dependencies

```bash
python -m pip install -r requirements.txt
```

---

## 🐍 Virtual environment activation (Windows + Bash)

If you have problems starting the server, make sure the virtual environment is active.

```bash
source .venv/Scripts/activate
```

You should see:

```text
(.venv)
```

Verify Python path:

```bash
which python
```

Expected output:

```text
/d/github_projects/intership-backend/.venv/Scripts/python
```

---

## 🚀 Run backend server

Preferred way:

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Alternative (may fail on Windows + Bash):

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 🧪 Testing

### Required dependency

Tests require **httpx**:

```bash
python -m pip install httpx
python -m pip show httpx
```

### Run tests (Windows)

```bash
PYTHONPATH=. .venv/Scripts/python -m pytest tests/
```

### Alternative (Unix-like systems)

```bash
pytest --rootdir=. tests/
pytest tests/
```

---

## ✅ Health check

After starting the server, open:

```text
http://localhost:8000/
```

Expected response:

```json
{
  "status_code": 200,
  "detail": "ok",
  "result": "working"
}
```
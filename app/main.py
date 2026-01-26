from fastapi import FastAPI

app = FastAPI(title="Internship Backend")

@app.get("/")
async def healthСheck():
  return {
    "status_code": 200,
    "detail": "ok",
    "result": "working"
  }
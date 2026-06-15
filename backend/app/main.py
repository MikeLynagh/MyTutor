from fastapi import FastAPI
from app.api import missions


app = FastAPI(title="Adaptive AI Tutor API")

app.include_router(missions.router, prefix="/api")

@app.get("/")
def read_root():
    return {"Hello Mike"}

@app.get("/health")
def get_health():
    return {"status":"ok"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}
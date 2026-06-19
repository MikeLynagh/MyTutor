from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import missions


app = FastAPI(title="Adaptive AI Tutor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(missions.router, prefix="/api")

@app.get("/")
def read_root():
    return {"Hello Mike"}

@app.get("/health")
def get_health():
    return {"status":"ok"}

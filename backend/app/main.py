from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from app.api import answers, lessons, mission_plan, missions


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
app.include_router(mission_plan.router, prefix="/api")
app.include_router(lessons.router, prefix="/api")
app.include_router(answers.router, prefix="/api")

@app.get("/")
def read_root():
    return {"Hello Mike"}

@app.get("/health")
def get_health():
    return {"status":"ok"}

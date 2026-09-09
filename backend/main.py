from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.check import router as check_router
from routers.extract import router as extract_router
from ddinter.router import router as ddinter_router
from routers.normalize import router as normalize_router
from routers.pipeline import router as pipeline_router

app = FastAPI(title="MedGuard Backend (A1 dev server)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to the real frontend URL once C has one
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(extract_router)
app.include_router(check_router)
app.include_router(ddinter_router)
app.include_router(normalize_router)
app.include_router(pipeline_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import settings
from app.routers.resume_router import router as resume_router
from app.routers.job_router import router as job_router
from app.routers.system import router as system_router

app = FastAPI(
    title="InterviewIQ API",
    description="AI-powered interview preparation platform API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(system_router)
app.include_router(resume_router)
app.include_router(job_router)

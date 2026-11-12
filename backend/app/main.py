from collections import defaultdict, deque
from time import monotonic

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from app.config.settings import settings
from app.routers.resume_router import router as resume_router
from app.routers.job_router import router as job_router
from app.routers.system import router as system_router
from app.routers.rag_router import router as rag_router
from app.routers.interview_router import router as interview_router
from app.routers.report_router import router as report_router

app = FastAPI(
    title="InterviewIQ API",
    description="AI-powered interview preparation platform API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)


class AIRateLimitMiddleware:
    expensive_prefixes = (
        "/api/v1/resumes/", "/api/v1/jobs/", "/api/v1/rag/", "/api/v1/interviews/"
    )

    def __init__(self, application, limit: int) -> None:
        self.application = application
        self.limit = limit
        self.requests: defaultdict[str, deque[float]] = defaultdict(deque)

    async def __call__(self, scope, receive, send):
        path = scope.get("path", "")
        method = scope.get("method", "GET")
        if method in {"POST", "PUT", "PATCH"} and path.startswith(self.expensive_prefixes):
            client = scope.get("client")
            client_key = client[0] if client else "unknown"
            now = monotonic()
            bucket = self.requests[client_key]
            while bucket and now - bucket[0] >= 60:
                bucket.popleft()
            if len(bucket) >= self.limit:
                response = JSONResponse(
                    {"detail": "Too many AI requests. Please try again later."},
                    status_code=429,
                    headers={"Retry-After": "60"},
                )
                await response(scope, receive, send)
                return
            bucket.append(now)
        await self.application(scope, receive, send)


app.add_middleware(AIRateLimitMiddleware, limit=settings.ai_rate_limit_per_minute)

app.include_router(system_router)
app.include_router(resume_router)
app.include_router(job_router)
app.include_router(rag_router)
app.include_router(interview_router)
app.include_router(report_router)

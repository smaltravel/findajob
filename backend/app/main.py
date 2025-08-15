from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from app.config.loader import settings
from app.routes.job_router import job_router
from app.routes.search_router import search_router

openapi_tags = [
    {
        "name": "Jobs",
        "description": "Job-related read operations"
    },
    {
        "name": "Search",
        "description": "Search-related operations"
    }
]

app = FastAPI(
    title="Find a Job API",
    openapi_tags=openapi_tags,
)

if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            str(origin).strip("/") for origin in settings.BACKEND_CORS_ORIGINS
        ],
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(job_router, prefix="/api", tags=["Jobs"])
app.include_router(search_router, prefix="/api", tags=["Search"])


@app.get("/health", tags=["Health Check"])
def health_check():
    return {"status": "ok"}


@app.get("/", tags=["Root"])
def root():
    return {"message": "Welcome to the Find a Job API"}

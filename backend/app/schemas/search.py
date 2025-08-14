from pydantic import BaseModel


class SpiderConfig(BaseModel):
    keywords: str
    location: str
    max_jobs: int
    seniority: int


class AIProviderConfig(BaseModel):
    provider: str
    model: str
    base_url: str
    api_key: str

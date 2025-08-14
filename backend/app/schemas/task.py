from pydantic import BaseModel
from app.schemas.search import SpiderConfig, AIProviderConfig


class SearchTaskResponse(BaseModel):
    id: int
    status: str


class SearchTaskRequest(BaseModel):
    spider_config: SpiderConfig
    ai_provider_config: AIProviderConfig

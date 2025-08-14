from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Annotated, Any, Literal

from pydantic import (
    AnyUrl,
    BeforeValidator,
    computed_field,
    PostgresDsn,
    Field
)

from pydantic_core import MultiHostUrl


def parse_cors(v: Any) -> list[str] | str:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)


class AppConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
        env_ignore_empty=True,
    )
    DOMAIN: Annotated[str, Field(alias="DOMAIN")] = "localhost"
    ENVIRONMENT: Annotated[Literal["local", "production"], Field(alias="ENVIRONMENT")] = "local"

    @computed_field
    @property
    def server_host(self) -> str:
        # Use HTTPS for anything other than local development
        if self.ENVIRONMENT == "local":
            return f"http://{self.DOMAIN}"
        return f"https://{self.DOMAIN}"

    BACKEND_CORS_ORIGINS: Annotated[
        list[AnyUrl] | str, BeforeValidator(parse_cors)
    ] = Field(default_factory=list)

    DB_HOST: Annotated[str, Field(alias="DB_HOST")] = "localhost"
    DB_PORT: Annotated[int, Field(alias="DB_PORT")] = 5432
    DB_USER: Annotated[str, Field(alias="DB_USER")] = "postgres"
    DB_PASSWORD: Annotated[str, Field(alias="DB_PASSWORD")] = "password"
    DB_NAME: Annotated[str, Field(alias="DB_NAME")] = "findajob"

    @computed_field
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> PostgresDsn:
        return MultiHostUrl.build(
            scheme="postgresql+psycopg2",
            user=self.DB_USER,
            password=self.DB_PASSWORD,
            host=self.DB_HOST,
            port=self.DB_PORT,
            path=self.DB_NAME,
        )

    CELERY_BROKER_URL: Annotated[str, Field(alias="CELERY_BROKER_URL")] = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND: Annotated[str, Field(alias="CELERY_RESULT_BACKEND")] = "redis://redis:6379/0"

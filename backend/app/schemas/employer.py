from pydantic import BaseModel, HttpUrl


class Employer(BaseModel):
    id: int
    name: str
    url: HttpUrl
    industries: str
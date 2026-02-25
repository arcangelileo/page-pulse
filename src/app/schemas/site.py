from datetime import datetime

from pydantic import BaseModel, Field


class SiteCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    domain: str = Field(..., min_length=1, max_length=255)


class SiteUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    domain: str | None = Field(None, min_length=1, max_length=255)
    public: bool | None = None


class SiteResponse(BaseModel):
    id: str
    name: str
    domain: str
    public: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SiteWithSnippet(SiteResponse):
    tracking_snippet: str

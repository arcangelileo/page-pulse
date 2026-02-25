from pydantic import BaseModel, Field


class EventPayload(BaseModel):
    s: str = Field(..., description="Site ID")
    u: str = Field(..., max_length=2048, description="Full URL")
    p: str = Field(..., max_length=2048, description="Path")
    r: str = Field("", max_length=2048, description="Referrer")
    sw: int = Field(0, ge=0, description="Screen width")
    us: str = Field("", max_length=255, description="utm_source")
    um: str = Field("", max_length=255, description="utm_medium")
    uc: str = Field("", max_length=255, description="utm_campaign")
    ut: str = Field("", max_length=255, description="utm_term")
    ux: str = Field("", max_length=255, description="utm_content")

"""
AI 家庭管家相关 Schema
"""
from datetime import datetime
from typing import Any, Literal, Optional
from uuid import UUID
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator


AIProviderStatus = Literal[
    "disabled",
    "active",
    "paused_billing_or_auth",
    "paused_rate_limit",
    "paused_error",
]
AIJobStatus = Literal["pending", "running", "completed", "failed", "skipped"]


class AIProviderBase(BaseModel):
    name: str = Field(default="默认模型", min_length=1, max_length=100)
    base_url: str = Field(default="https://api.openai.com/v1", min_length=1, max_length=500)
    text_model: str = Field(default="gpt-4o-mini", min_length=1, max_length=120)
    vision_model: Optional[str] = Field(None, max_length=120)
    timeout_seconds: int = Field(default=30, ge=5, le=120)
    enabled: bool = False

    @field_validator("base_url")
    @classmethod
    def normalize_base_url(cls, value: str) -> str:
        cleaned = value.strip().rstrip("/")
        parsed = urlparse(cleaned)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("Base URL 必须是有效的 http/https 地址")
        return cleaned


class AIProviderUpdate(AIProviderBase):
    api_key: Optional[str] = Field(None, max_length=5000)


class AIProviderResponse(AIProviderBase):
    id: UUID
    status: AIProviderStatus | str
    has_api_key: bool
    failure_count: int
    last_error: Optional[str] = None
    paused_reason: Optional[str] = None
    last_checked_at: Optional[datetime] = None
    notified_pause_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AIProviderTestResponse(BaseModel):
    ok: bool
    status: AIProviderStatus | str
    message: str


class AIPersonaBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    avatar_url: Optional[str] = Field(None, max_length=500)
    persona_type: str = Field(default="steward", max_length=50)
    tone: Optional[str] = Field(None, max_length=500)
    bio: Optional[str] = None
    enabled: bool = True
    auto_comment_enabled: bool = True
    report_enabled: bool = True
    album_suggestion_enabled: bool = True
    sort_order: int = 0


class AIPersonaCreate(AIPersonaBase):
    pass


class AIPersonaUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=80)
    avatar_url: Optional[str] = Field(None, max_length=500)
    persona_type: Optional[str] = Field(None, max_length=50)
    tone: Optional[str] = Field(None, max_length=500)
    bio: Optional[str] = None
    enabled: Optional[bool] = None
    auto_comment_enabled: Optional[bool] = None
    report_enabled: Optional[bool] = None
    album_suggestion_enabled: Optional[bool] = None
    sort_order: Optional[int] = None


class AIPersonaResponse(AIPersonaBase):
    id: UUID
    user_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AIStatusResponse(BaseModel):
    enabled: bool
    status: AIProviderStatus | str
    provider: Optional[AIProviderResponse] = None
    personas_enabled: int
    auto_comment_personas: int


class AIJobResponse(BaseModel):
    id: UUID
    job_type: str
    status: AIJobStatus | str
    target_type: Optional[str] = None
    target_id: Optional[UUID] = None
    persona_id: Optional[UUID] = None
    progress_current: int
    progress_total: int
    retry_count: int
    max_retries: int
    error_message: Optional[str] = None
    result: dict[str, Any] = Field(default_factory=dict)
    created_by: Optional[UUID] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AIJobCreate(BaseModel):
    job_type: Literal["history_learning", "album_suggestions"] = "history_learning"


class AIProfileUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=120)
    summary: Optional[str] = None
    traits: Optional[list[str]] = None
    preferences: Optional[list[str]] = None
    memories: Optional[list[str]] = None
    editable_notes: Optional[str] = None


class AIProfileResponse(BaseModel):
    id: UUID
    subject_type: str
    subject_id: Optional[UUID] = None
    title: str
    summary: Optional[str] = None
    traits: list[str] = Field(default_factory=list)
    preferences: list[str] = Field(default_factory=list)
    memories: list[str] = Field(default_factory=list)
    editable_notes: Optional[str] = None
    updated_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AIReportGenerateRequest(BaseModel):
    period_type: Literal["week", "month", "custom"] = "week"
    period_start: datetime
    period_end: datetime
    persona_id: Optional[UUID] = None


class AIReportUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=160)
    content: Optional[str] = Field(None, min_length=1)


class AIReportDraftResponse(BaseModel):
    id: UUID
    persona_id: Optional[UUID] = None
    period_type: str
    period_start: datetime
    period_end: datetime
    title: str
    content: str
    status: str
    source_metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: Optional[UUID] = None
    published_post_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AIAlbumSuggestionResponse(BaseModel):
    id: UUID
    target_type: str
    target_id: UUID
    album_id: Optional[UUID] = None
    suggested_album_name: Optional[str] = None
    reason: Optional[str] = None
    status: str
    created_by_persona_id: Optional[UUID] = None
    reviewed_by: Optional[UUID] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AIAlbumSuggestionReview(BaseModel):
    action: Literal["approve", "reject"]
    album_id: Optional[UUID] = None
    album_name: Optional[str] = Field(None, min_length=1, max_length=100)


class AISearchResponseItem(BaseModel):
    target_type: str
    target_id: UUID
    summary: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    scenes: list[str] = Field(default_factory=list)
    people: list[str] = Field(default_factory=list)
    score: int = 0


class AISearchResponse(BaseModel):
    query: str
    results: list[AISearchResponseItem]
    total: int

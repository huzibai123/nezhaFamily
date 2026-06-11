"""
AI 家庭管家相关模型
"""
from datetime import datetime, timezone
import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.db.base import Base

AI_COMMENT_STYLE_VALUES = {"warm", "gentle", "playful", "brief"}
AI_COMMENT_LENGTH_VALUES = {"short", "medium"}
AI_INTERACTION_FREQUENCY_VALUES = {"low", "normal", "high"}


class AIProviderConfig(Base):
    """OpenAI-compatible 模型供应商配置。"""

    __tablename__ = "ai_provider_configs"
    __table_args__ = (
        Index("idx_ai_provider_configs_enabled", "enabled"),
        Index("idx_ai_provider_configs_status", "status"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, default="默认模型")
    base_url = Column(String(500), nullable=False)
    api_key_encrypted = Column(Text, nullable=True)
    text_model = Column(String(120), nullable=False)
    vision_model = Column(String(120), nullable=True)
    timeout_seconds = Column(Integer, nullable=False, default=30)
    enabled = Column(Boolean, nullable=False, default=False)
    status = Column(String(40), nullable=False, default="disabled")
    failure_count = Column(Integer, nullable=False, default=0)
    last_error = Column(Text, nullable=True)
    paused_reason = Column(String(80), nullable=True)
    last_checked_at = Column(DateTime(timezone=True), nullable=True)
    notified_pause_at = Column(DateTime(timezone=True), nullable=True)
    settings = Column(JSONB, nullable=False, default=dict)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class AIPersona(Base):
    """可见的 AI 家庭角色。"""

    __tablename__ = "ai_personas"
    __table_args__ = (
        Index("idx_ai_personas_enabled", "enabled"),
        Index("idx_ai_personas_user_id", "user_id"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(80), nullable=False)
    avatar_url = Column(String(500), nullable=True)
    persona_type = Column(String(50), nullable=False, default="steward")
    tone = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    enabled = Column(Boolean, nullable=False, default=True)
    auto_comment_enabled = Column(Boolean, nullable=False, default=True)
    report_enabled = Column(Boolean, nullable=False, default=True)
    album_suggestion_enabled = Column(Boolean, nullable=False, default=True)
    sort_order = Column(Integer, nullable=False, default=0)
    persona_metadata = Column("metadata", JSONB, nullable=False, default=dict)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user = relationship("User", foreign_keys=[user_id])

    def _metadata_dict(self) -> dict:
        return self.persona_metadata if isinstance(self.persona_metadata, dict) else {}

    def _metadata_value(self, key: str, default: str, allowed: set[str]) -> str:
        value = self._metadata_dict().get(key, default)
        return value if value in allowed else default

    def _set_metadata_value(self, key: str, value: str, default: str, allowed: set[str]) -> None:
        metadata = dict(self.persona_metadata or {})
        metadata[key] = value if value in allowed else default
        self.persona_metadata = metadata

    @property
    def auto_like_enabled(self) -> bool:
        return bool(self._metadata_dict().get("auto_like_enabled", True))

    @auto_like_enabled.setter
    def auto_like_enabled(self, value: bool) -> None:
        metadata = dict(self.persona_metadata or {})
        metadata["auto_like_enabled"] = bool(value)
        self.persona_metadata = metadata

    @property
    def comment_style(self) -> str:
        return self._metadata_value("comment_style", "warm", AI_COMMENT_STYLE_VALUES)

    @comment_style.setter
    def comment_style(self, value: str) -> None:
        self._set_metadata_value("comment_style", value, "warm", AI_COMMENT_STYLE_VALUES)

    @property
    def comment_length(self) -> str:
        return self._metadata_value("comment_length", "short", AI_COMMENT_LENGTH_VALUES)

    @comment_length.setter
    def comment_length(self, value: str) -> None:
        self._set_metadata_value("comment_length", value, "short", AI_COMMENT_LENGTH_VALUES)

    @property
    def interaction_frequency(self) -> str:
        return self._metadata_value(
            "interaction_frequency",
            "low",
            AI_INTERACTION_FREQUENCY_VALUES,
        )

    @interaction_frequency.setter
    def interaction_frequency(self, value: str) -> None:
        self._set_metadata_value(
            "interaction_frequency",
            value,
            "low",
            AI_INTERACTION_FREQUENCY_VALUES,
        )


class AIJob(Base):
    """AI 后台任务记录。"""

    __tablename__ = "ai_jobs"
    __table_args__ = (
        Index("idx_ai_jobs_type_status", "job_type", "status"),
        Index("idx_ai_jobs_created_at", "created_at"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_type = Column(String(50), nullable=False)
    status = Column(String(30), nullable=False, default="pending")
    target_type = Column(String(50), nullable=True)
    target_id = Column(UUID(as_uuid=True), nullable=True)
    persona_id = Column(UUID(as_uuid=True), ForeignKey("ai_personas.id", ondelete="SET NULL"), nullable=True)
    progress_current = Column(Integer, nullable=False, default=0)
    progress_total = Column(Integer, nullable=False, default=0)
    retry_count = Column(Integer, nullable=False, default=0)
    max_retries = Column(Integer, nullable=False, default=3)
    error_message = Column(Text, nullable=True)
    result = Column(JSONB, nullable=False, default=dict)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    persona = relationship("AIPersona")
    creator = relationship("User", foreign_keys=[created_by])


class AIContentInsight(Base):
    """帖子或媒体的 AI 理解结果。"""

    __tablename__ = "ai_content_insights"
    __table_args__ = (
        Index("idx_ai_content_insights_target", "target_type", "target_id"),
        Index("idx_ai_content_insights_created_at", "created_at"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    target_type = Column(String(50), nullable=False)
    target_id = Column(UUID(as_uuid=True), nullable=False)
    summary = Column(Text, nullable=True)
    tags = Column(JSONB, nullable=False, default=list)
    scenes = Column(JSONB, nullable=False, default=list)
    people = Column(JSONB, nullable=False, default=list)
    sentiment = Column(String(40), nullable=True)
    model_metadata = Column(JSONB, nullable=False, default=dict)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class AIProfile(Base):
    """家庭或成员画像。"""

    __tablename__ = "ai_profiles"
    __table_args__ = (
        Index("idx_ai_profiles_subject", "subject_type", "subject_id"),
        Index("idx_ai_profiles_updated_at", "updated_at"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subject_type = Column(String(30), nullable=False)
    subject_id = Column(UUID(as_uuid=True), nullable=True)
    title = Column(String(120), nullable=False)
    summary = Column(Text, nullable=True)
    traits = Column(JSONB, nullable=False, default=list)
    preferences = Column(JSONB, nullable=False, default=list)
    memories = Column(JSONB, nullable=False, default=list)
    editable_notes = Column(Text, nullable=True)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updater = relationship("User", foreign_keys=[updated_by])


class AIAlbumSuggestion(Base):
    """AI 相册整理建议。"""

    __tablename__ = "ai_album_suggestions"
    __table_args__ = (
        Index("idx_ai_album_suggestions_status", "status"),
        Index("idx_ai_album_suggestions_target", "target_type", "target_id"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    target_type = Column(String(50), nullable=False)
    target_id = Column(UUID(as_uuid=True), nullable=False)
    album_id = Column(UUID(as_uuid=True), ForeignKey("albums.id", ondelete="SET NULL"), nullable=True)
    suggested_album_name = Column(String(100), nullable=True)
    reason = Column(Text, nullable=True)
    status = Column(String(30), nullable=False, default="pending")
    created_by_persona_id = Column(UUID(as_uuid=True), ForeignKey("ai_personas.id", ondelete="SET NULL"), nullable=True)
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    persona = relationship("AIPersona")
    reviewer = relationship("User", foreign_keys=[reviewed_by])


class AIReportDraft(Base):
    """AI 回忆报告草稿。"""

    __tablename__ = "ai_report_drafts"
    __table_args__ = (
        Index("idx_ai_report_drafts_status", "status"),
        Index("idx_ai_report_drafts_period", "period_type", "period_start", "period_end"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    persona_id = Column(UUID(as_uuid=True), ForeignKey("ai_personas.id", ondelete="SET NULL"), nullable=True)
    period_type = Column(String(20), nullable=False)
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    title = Column(String(160), nullable=False)
    content = Column(Text, nullable=False)
    status = Column(String(30), nullable=False, default="draft")
    source_metadata = Column(JSONB, nullable=False, default=dict)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    published_post_id = Column(UUID(as_uuid=True), ForeignKey("posts.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    persona = relationship("AIPersona")
    creator = relationship("User", foreign_keys=[created_by])

"""
家庭设置模型
保存全局展示所需的单行配置
"""

from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class FamilySettings(Base):
    """家庭设置表（单行）"""

    __tablename__ = "family_settings"
    __table_args__ = (CheckConstraint("id = 1", name="ck_family_settings_single_row"),)

    id = Column(Integer, primary_key=True, default=1)
    family_name = Column(String(100), nullable=False, default="哪吒家庭")
    tagline = Column(String(200), nullable=True)
    theme_color = Column(String(20), nullable=True)
    accent_color = Column(String(20), nullable=True)
    background_image_url = Column(String(500), nullable=True)
    logo_url = Column(String(500), nullable=True)
    theme_assets = Column(JSONB, nullable=False, default=dict)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
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

    updater = relationship("User")

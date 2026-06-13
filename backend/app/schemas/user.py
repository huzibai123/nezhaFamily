"""
用户相关的 Pydantic Schema
用于请求验证和响应序列化
"""
import re
from typing import Optional
from datetime import datetime, date
from pydantic import BaseModel, Field, field_validator
from uuid import UUID

from app.core.password_policy import validate_password_strength


class UserBase(BaseModel):
    """用户基础字段"""
    username: str = Field(..., min_length=2, max_length=50, description="用户名")
    email: str = Field(..., min_length=5, max_length=100, description="邮箱地址")


class UserCreate(UserBase):
    """用户注册请求"""
    password: str = Field(..., min_length=10, max_length=100, description="密码（至少10位，包含字母和数字）")
    invite_code: str = Field(..., min_length=8, max_length=32, description="邀请码")

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """验证用户名格式：只允许字母、数字、下划线、中文"""
        if not re.match(r'^[a-zA-Z0-9_一-鿿]+$', v):
            raise ValueError("用户名只能包含字母、数字、下划线和中文")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str, info) -> str:
        data = info.data
        return validate_password_strength(
            v,
            username=data.get("username"),
            email=data.get("email"),
        )


class UserLogin(BaseModel):
    """用户登录请求"""
    username: str = Field(..., description="用户名或邮箱")
    password: str = Field(..., description="密码")


class UserResponse(UserBase):
    """用户信息响应（公开字段）"""
    id: UUID
    role: str
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    birthday: Optional[date] = None
    role_in_family: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class UserProfile(UserResponse):
    """用户详细信息（包含更多私有字段）"""
    invite_code: Optional[str] = None
    invited_by: Optional[UUID] = None
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserProfileUpdate(BaseModel):
    """用户档案更新请求"""
    avatar_url: Optional[str] = Field(None, max_length=500, description="头像 URL")
    bio: Optional[str] = Field(None, max_length=500, description="个人简介")
    birthday: Optional[date] = Field(None, description="生日")
    role_in_family: Optional[str] = Field(None, max_length=50, description="家庭角色")


class UserStatsResponse(BaseModel):
    """用户统计信息"""
    post_count: int = Field(..., description="发帖数")
    comment_count: int = Field(..., description="评论数")
    like_count: int = Field(..., description="获赞数")


class TokenResponse(BaseModel):
    """登录成功响应"""
    access_token: str = Field(..., description="JWT Access Token")
    token_type: str = Field(default="bearer", description="Token 类型")
    user: UserResponse


class InviteCodeCreate(BaseModel):
    """生成邀请码请求（管理员功能）"""
    expires_days: int = Field(default=30, ge=1, le=365, description="有效天数")


class InviteCodeResponse(BaseModel):
    """邀请码响应"""
    code: str
    expires_at: datetime
    created_by: UUID


class InviteLookupResponse(BaseModel):
    """公开的邀请码校验响应"""
    valid: bool
    message: str

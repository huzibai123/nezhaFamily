"""
点赞相关的 Pydantic Schema
用于请求验证和响应序列化
"""
from pydantic import BaseModel


class LikeResponse(BaseModel):
    """点赞响应"""
    success: bool
    liked: bool  # True=已点赞，False=已取消点赞
    like_count: int  # 当前点赞数

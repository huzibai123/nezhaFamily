"""
通用响应模型（已废弃）

DEPRECATED: 项目约定不使用 {success, data, message} 封装
以下类保留供参考，新代码不应使用
"""
from typing import Generic, TypeVar, Optional
from pydantic import BaseModel, Field

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """
    统一 API 响应格式

    使用示例:
        return APIResponse(success=True, data=user, message="操作成功")
    """

    success: bool = Field(..., description="操作是否成功")
    data: Optional[T] = Field(None, description="返回的数据")
    message: str = Field(default="", description="提示信息")


class PaginatedResponse(BaseModel, Generic[T]):
    """
    分页响应模型

    使用示例:
        return PaginatedResponse(
            items=posts,
            total=100,
            page=1,
            page_size=20
        )
    """

    items: list[T] = Field(..., description="数据列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")
    total_pages: int = Field(..., description="总页数")

    @classmethod
    def create(cls, items: list[T], total: int, page: int, page_size: int):
        """创建分页响应"""
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

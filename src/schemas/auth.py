"""认证相关数据模型"""

from datetime import datetime
from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    """用户注册请求模型"""

    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="用户名"
    )
    password: str = Field(
        ...,
        min_length=6,
        max_length=100,
        description="密码"
    )


class UserLogin(BaseModel):
    """用户登录请求模型"""

    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class Token(BaseModel):
    """JWT Token 响应模型"""

    access_token: str = Field(..., description="JWT 访问令牌")
    token_type: str = Field(default="bearer", description="Token 类型")


class TokenData(BaseModel):
    """Token 中的用户数据"""

    user_id: str = Field(..., description="用户 ID")
    username: str = Field(..., description="用户名")


class User(BaseModel):
    """用户信息模型"""

    user_id: str = Field(..., description="用户 ID")
    username: str = Field(..., description="用户名")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")


class UserInDB(User):
    """数据库中的用户模型 (含密码哈希)"""

    hashed_password: str = Field(..., description="密码哈希")

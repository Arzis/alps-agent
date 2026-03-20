"""认证路由 - 处理用户注册、登录和 Token 验证"""

import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt
from passlib.context import CryptContext

from src.schemas.auth import Token, TokenData, User, UserCreate, UserInDB
from src.infra.config.settings import get_settings
from src.api.dependencies import get_pg_pool

router = APIRouter(prefix="/auth", tags=["Authentication"])

# 密码哈希上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """哈希密码"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """创建 JWT Token"""
    settings = get_settings()
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


async def get_user_by_username(username: str, pg_pool) -> UserInDB | None:
    """从数据库获取用户"""
    async with pg_pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT user_id, username, hashed_password, created_at FROM users WHERE username = $1",
            username
        )
        if row:
            return UserInDB(
                user_id=row["user_id"],
                username=row["username"],
                hashed_password=row["hashed_password"],
                created_at=row["created_at"]
            )
        return None


async def get_user_by_id(user_id: str, pg_pool) -> UserInDB | None:
    """从数据库获取用户 by ID"""
    async with pg_pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT user_id, username, hashed_password, created_at FROM users WHERE user_id = $1",
            user_id
        )
        if row:
            return UserInDB(
                user_id=row["user_id"],
                username=row["username"],
                hashed_password=row["hashed_password"],
                created_at=row["created_at"]
            )
        return None


async def create_user(username: str, password: str, pg_pool) -> UserInDB:
    """创建新用户"""
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    hashed_password = get_password_hash(password)

    async with pg_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO users (user_id, username, hashed_password, created_at)
            VALUES ($1, $2, $3, $4)
            """,
            user_id, username, hashed_password, datetime.utcnow()
        )

    return UserInDB(
        user_id=user_id,
        username=username,
        hashed_password=hashed_password,
        created_at=datetime.utcnow()
    )


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    pg_pool = Depends(get_pg_pool),
) -> TokenData:
    """获取当前登录用户 (从 JWT Token)"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        username: str = payload.get("username")
        if user_id is None or username is None:
            raise credentials_exception
    except jwt.JWTError:
        raise credentials_exception

    user = await get_user_by_id(user_id, pg_pool)
    if user is None:
        raise credentials_exception

    return TokenData(user_id=user_id, username=username)


@router.post("/register", response_model=User)
async def register(
    user_data: UserCreate,
    pg_pool = Depends(get_pg_pool),
):
    """用户注册

    Args:
        user_data: 用户注册信息
        pg_pool: PostgreSQL 连接池

    Returns:
        User: 创建的用户信息

    Raises:
        HTTPException: 如果用户名已存在
    """
    # 检查用户名是否已存在
    existing_user = await get_user_by_username(user_data.username, pg_pool)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    # 创建用户
    user = await create_user(user_data.username, user_data.password, pg_pool)

    return User(
        user_id=user.user_id,
        username=user.username,
        created_at=user.created_at
    )


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    pg_pool = Depends(get_pg_pool),
):
    """用户登录

    Args:
        form_data: OAuth2 密码表单 (username, password)
        pg_pool: PostgreSQL 连接池

    Returns:
        Token: JWT 访问令牌

    Raises:
        HTTPException: 如果用户名或密码错误
    """
    user = await get_user_by_username(form_data.username, pg_pool)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    settings = get_settings()
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.user_id, "username": user.username},
        expires_delta=access_token_expires
    )

    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=User)
async def get_current_user_info(
    current_user: TokenData = Depends(get_current_user),
    pg_pool = Depends(get_pg_pool),
):
    """获取当前用户信息

    Args:
        current_user: 当前登录用户 (从 token 解析)
        pg_pool: PostgreSQL 连接池

    Returns:
        User: 用户信息
    """
    user = await get_user_by_id(current_user.user_id, pg_pool)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return User(
        user_id=user.user_id,
        username=user.username,
        created_at=user.created_at
    )

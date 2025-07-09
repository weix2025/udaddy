# app/core/security.py

from datetime import datetime, timedelta
from typing import Any, Union

from jose import jwt, JWTError
from passlib.context import CryptContext

from app.core.config import settings

# 创建一个密码哈希上下文实例
# "bcrypt" 是目前推荐的、安全性很高的哈希算法
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 从配置中获取JWT算法
ALGORITHM = settings.ALGORITHM

def create_access_token(
    subject: Union[str, Any], expires_delta: timedelta = None
) -> str:
    """
    创建一个新的JWT Access Token。
    :param subject: Token的主题，通常是用户的唯一标识（如用户ID）。
    :param expires_delta: Token的有效时间。如果未提供，则使用配置文件中的默认值。
    :return: 加密后的JWT字符串。
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        # 计算过期时间
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    # 准备要编码到Token中的数据 (payload)
    to_encode = {"exp": expire, "sub": str(subject)}
    # 使用SECRET_KEY和指定的算法进行编码
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证明文密码是否与哈希后的密码匹配。
    :param plain_password: 用户提交的明文密码。
    :param hashed_password: 数据库中存储的哈希密码。
    :return: 匹配则返回True，否则返回False。
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    将明文密码进行哈希加密。
    :param password: 要加密的明文密码。
    :return: 哈希后的密码字符串。
    """
    return pwd_context.hash(password)
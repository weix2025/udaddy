# app/core/config.py
from pydantic_settings import BaseSettings

from pydantic import PostgresDsn, RedisDsn, EmailStr

class Settings(BaseSettings):
    # --- 项目元数据 ---
    PROJECT_NAME: str = "Netbase - AI Workflow Engine"
    API_V1_STR: str = "/api/v1"

    # --- JWT认证相关配置 ---
    # 在生产环境中，这应该是一个非常复杂且通过环境变量注入的密钥
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    # 访问令牌的有效期（分钟）
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8 # 8天

    # --- 数据库连接配置 ---
    # 使用Pydantic的PostgresDsn进行验证
    DATABASE_URL: PostgresDsn

    # --- Redis连接配置 ---
    # 使用Pydantic的RedisDsn进行验证
    REDIS_URL: RedisDsn

    # --- 初始超级用户信息 ---
    # 这些值应该通过环境变量在首次启动时设置
    FIRST_SUPERUSER: str
    FIRST_SUPERUSER_PASSWORD: str
    FIRST_SUPERUSER_EMAIL: EmailStr

    class Config:
        # Pydantic将自动从.env文件和环境变量中读取配置
        env_file = ".env"
        env_file_encoding = 'utf-8'
        case_sensitive = True

settings = Settings()
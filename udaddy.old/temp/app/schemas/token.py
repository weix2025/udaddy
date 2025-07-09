# app/schemas/token.py

from pydantic import BaseModel

class Token(BaseModel):
    """
    用于登录成功后返回JWT的模型。
    """
    access_token: str
    token_type: str

class TokenPayload(BaseModel):
    """
    用于解析JWT payload内容的模型。
    确保payload中包含我们期望的字段（subject，即用户ID）。
    """
    sub: int | None = None
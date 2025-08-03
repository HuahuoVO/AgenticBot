# 定义请求体模型
from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
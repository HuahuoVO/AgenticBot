import logging

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

# 设置日志级别为 ERROR，这样会忽略 WARNING 及以下级别的日志
logging.basicConfig(level=logging.ERROR)
from api.chat import chat_agents, chat_stream
from models.request_model import ChatRequest

app = FastAPI()

@app.post("/chat")
def chat_endpoint(request: ChatRequest):
    return StreamingResponse(
        chat_agents(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
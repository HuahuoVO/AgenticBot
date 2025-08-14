import logging

import pydantic
from dataclasses_json.mm import JsonData
from langchain_openai import ChatOpenAI
from starlette.responses import StreamingResponse
# 设置日志级别为 ERROR，这样会忽略 WARNING 及以下级别的日志
logging.basicConfig(level=logging.ERROR)
from agent import context
from agent.agent import create_agentic_bot, parse_message_chunk
from agent.context import create_context
from models.request_model import ChatRequest
from langchain_ollama import ChatOllama
import json
# llm = ChatOllama(
#     model="mistral"
# )
print(pydantic.VERSION)
llm = ChatOpenAI(
    #openai_api_base="https://jeniya.top/v1",
    #model="gpt-4o-2024-11-20",
    # openai_api_key="sk-Pdgb7598A7DmoYMg5rWyZOa0umC7xS5Z4INVzyuRzoWko5Xo"
    openai_api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
    model="qwen-flash",
    openai_api_key="sk-c6c42fbb1c6e4f42b7323c8537a08a1c"
)
# llm = ChatOpenAI(
#     openai_api_base="https://ark.cn-beijing.volces.com/api/v3",
#     model="doubao-1-5-pro-32k-250115",
#     openai_api_key="50436179-01ec-4441-831d-6e244398a7ef"
# )
def chat(request: ChatRequest):
    supervisor = create_agentic_bot(llm=llm)
    for agent, event, data in supervisor.stream(
            stream_mode=["messages", "updates"],
            input=
            {
                "messages": [
                    {
                        "role": "user",
                        "content": request.message
                    }
                ]
            },
            subgraphs=True,
            config={
                "recursion_limit": 65536,
            },
    ):
        context = create_context()
        content = parse_message_chunk(event, agent, data, context)
        for msg in content:
            print(f"msg: {msg.model_dump_json()}")

if __name__ == "__main__":
    req = ChatRequest(
        message="北京今天天气怎么样? 生活指数怎么样？"
    )
    chat(req)
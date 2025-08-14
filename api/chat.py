import logging

from dataclasses_json.mm import JsonData
from langchain_openai import ChatOpenAI

from fastapi.responses import StreamingResponse
from openai import OpenAI

from agent import context
from agent.agent import create_agentic_bot, parse_message_chunk
from agent.context import create_context
from models.request_model import ChatRequest
from langchain_ollama import ChatOllama
import json
# llm = ChatOllama(
#     model="mistral"
# )
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
def chat_agents(request: ChatRequest):
    supervisor = create_agentic_bot(llm=llm)
    def chat_generator():

        for agent, event, data in supervisor.stream(
                stream_mode=["messages", "updates", "values"],
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
                yield f"data: {msg.model_dump_json()} \n\n"
    return chat_generator()

def chat_stream(request: ChatRequest):
    client = OpenAI(
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",

        api_key="sk-c6c42fbb1c6e4f42b7323c8537a08a1c"
    )
    def generator():
        completion = client.chat.completions.create(
            # 模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
            model="qwen-flash",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": request.message},
            ],
            # Qwen3模型通过enable_thinking参数控制思考过程（开源版默认True，商业版默认False）
            # 使用Qwen3开源版模型时，若未启用流式输出，请将下行取消注释，否则会报错
            # extra_body={"enable_thinking": False},
            stream=True
        )
        for chunk in completion:
            yield f"data: {chunk.model_dump_json()} \n\n"
    return generator()

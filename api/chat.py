from dataclasses_json.mm import JsonData
from langchain_openai import ChatOpenAI
from starlette.responses import StreamingResponse

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
    openai_api_base="https://jeniya.top/v1",
    model="gpt-4o-2024-11-20",
    openai_api_key="sk-Pdgb7598A7DmoYMg5rWyZOa0umC7xS5Z4INVzyuRzoWko5Xo"
)
# llm = ChatOpenAI(
#     openai_api_base="https://ark.cn-beijing.volces.com/api/v3",
#     model="doubao-1-5-pro-32k-250115",
#     openai_api_key="50436179-01ec-4441-831d-6e244398a7ef"
# )
def chat(request: ChatRequest):
    supervisor = create_agentic_bot(llm=llm)
    def chat_generator():

        for agent, event, data in supervisor.stream(
                stream_mode=["messages"],
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
            content = parse_message_chunk(agent, event, data, context)


            yield f"data: {json.dumps(content)}"

        # 流结束标记
        yield "data: [DONE]\n\n"
    return StreamingResponse(chat_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    req = ChatRequest(
        message="北京今天天气怎么样? 生活指数怎么样？"
    )
    chat(req)
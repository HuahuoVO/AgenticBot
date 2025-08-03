from langchain_openai import ChatOpenAI

from agent.agent import create_agentic_bot
from models.request_model import ChatRequest
from langchain_ollama import ChatOllama

llm = ChatOllama(
    model="gemma3:1B"
)
llm = ChatOpenAI(
    base_url = "https://ark.cn-beijing.volces.com/api/v3",
    model="doubao-seed-1-6-250615",
    api_key="50436179-01ec-4441-831d-6e244398a7ef"
)

def chat(request: ChatRequest):

    supervisor = create_agentic_bot(llm=llm)
    for agent, event, data in supervisor.stream(
            stream_mode=["values", "updates", "messages"],
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
                "recursion_limit": 10,
            },
    ):
        #context = create_context()
        #contents = parse_message_chunk(agent, event, data, context)
        print(f"agent: {agent} event: {event} data: {data}")



if __name__ == "__main__":
    req = ChatRequest(
        message="北京今天天气怎么样"
    )
    chat(req)
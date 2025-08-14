from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor
llm = ChatOpenAI(
    openai_api_base="https://jeniya.top/v1",
    model="gpt-4o-2024-11-20",
    openai_api_key="sk-ljc7hV7NriG1QGiyOzqlXrwbeBUbJlFIaoLPxoeFHOj6DEAF"
)
def book_hotel(hotel_name: str):
    """Book a hotel"""
    return f"Successfully booked a stay at {hotel_name}."

def book_flight(from_airport: str, to_airport: str):
    """Book a flight"""
    return f"Successfully booked a flight from {from_airport} to {to_airport}."

flight_assistant = create_react_agent(
    model=llm,
    tools=[book_flight],
    prompt="You are a flight booking assistant",
    name="flight_assistant"
)

hotel_assistant = create_react_agent(
    model=llm,
    tools=[book_hotel],
    prompt="You are a hotel booking assistant",
    name="hotel_assistant"
)

supervisor = create_supervisor(
    agents=[flight_assistant, hotel_assistant],
    model=llm,
    prompt=(
        "You manage a hotel booking assistant and a"
        "flight booking assistant. Assign work to them."
    )
).compile()

for agent, event, data in supervisor.stream(
        stream_mode=["values", "updates", "messages"],
        input=
        {
            "messages": [
                {
                    "role": "user",
                    "content": "book a flight from BOS to JFK and a stay at McKittrick Hotel"
                }
            ]
        },
        subgraphs=True,
        config={
            "recursion_limit": 65536,
        },
):
    print(agent, event, data)
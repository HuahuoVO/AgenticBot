import json
import logging
from typing import cast, List, Any


from langchain_core.messages import ToolMessage, BaseMessage, AIMessage, AIMessageChunk
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI
from langgraph._internal._runnable import RunnableCallable
from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor
from pydantic import BaseModel
import models.types
from .context import get_tool_call_info, remove_tool_call_info, set_final_message, add_tool_call_info

from models.events import ToolCallStartEvent, ToolCallArgsEvent, ToolCallResultEvent, TextMessageContentEvent, \
    TextMessageEndEvent
from tools.mcp_tools import get_real_time_weather, get_life_index

from agent.State import AgenticBotState
from agent.hooks import pre_tool_caller_hook, get_post_tool_caller_hook, post_planner_hook, pre_planner_hook
from agent.prompts import tool_call_system_prompt, supervisor_prompt, planner_system_prompt, \
    summary_agent_system_prompt, supervisor_system_prompt


def parse_message_chunk(event, agent, data, context) -> List[BaseModel]:
    stream_msgs = []
    if event == "messages":
        chunk, metadata = cast(tuple[BaseMessage, dict[str, Any]], data)
        name = chunk.name
        if not name and agent:
            name = agent[0].split(":")[0]
        logging.info(f"Chunk {chunk.name} received")
        if isinstance(chunk, AIMessageChunk):
            logging.debug(f"Tool call chunks: {chunk.tool_call_chunks}")
            if chunk.tool_call_chunks:
                tool_call = chunk.tool_call_chunks[0]
                index = tool_call["index"]
                tool_call_info = get_tool_call_info(
                    context, index=index, tool_call_id=None
                )
                if not tool_call_info:
                    add_tool_call_info(
                        context,
                        index,
                        {
                            "id": tool_call["id"],
                            "name": tool_call["name"],
                        },
                    )
                    stream_msgs.append(
                        ToolCallStartEvent(
                            tool_call_id=tool_call["id"],
                            tool_call_name=tool_call['name'] if tool_call['name'] is not None else '-',
                        )
                    )
                else:
                    stream_msgs.append(
                        ToolCallArgsEvent(
                            delta=tool_call["args"],
                            tool_call_id=tool_call_info["id"],
                            tool_call_name=tool_call_info['name'] if tool_call_info['name'] is not None else '-',
                        )
                    )
            else:

                if chunk.content:
                    if name == "summary_agent":
                        stream_msgs.append(
                            TextMessageEndEvent(
                                delta=json.dumps(chunk.content),
                                message_id=chunk.id,
                                name=name,
                                role=models.types.MessageRoleEnum.AI,
                            )
                        )
                        set_final_message(context)
                    else:
                        stream_msgs.append(
                            TextMessageContentEvent(
                                delta=json.dumps(chunk.content),
                                message_id=chunk.id,
                                name=name,
                                role=models.types.MessageRoleEnum.AI,
                            )
                        )
        elif isinstance(chunk, AIMessage):
            if chunk.content:
                stream_msgs.append(
                    TextMessageContentEvent(
                        delta=json.dumps(chunk.content),
                        messageId=chunk.id,
                        name=chunk.name,
                        role=models.types.MessageRoleEnum.AI,
                    )
                )
        elif isinstance(chunk, ToolMessage):
            tool_call_id = chunk.id
            tool_call_name = chunk.name
            # 移除tool_call_id
            delete = remove_tool_call_info(context, tool_call_id)
            if not delete:
                stream_msgs.append(
                    ToolCallStartEvent(
                        tool_call_id=tool_call_id,
                        tool_call_name=tool_call_name,
                    )
                )
                stream_msgs.append(
                    ToolCallArgsEvent(
                        delta="{}",
                        tool_call_id=tool_call_id,
                        tool_call_name=tool_call_name,
                    )
                )

            stream_msgs.append(
                ToolCallResultEvent(
                    delta=json.dumps(chunk.content),
                    tool_call_id=tool_call_id,
                    tool_call_name=tool_call_name,
                    tool_call_status=chunk.status,
                )
            )
        else:
            print(f"unknown chunk type:{chunk.__class__.__name__}")
    elif event == "updates":
        for k, v in data.items():
            if not isinstance(v, dict):
                continue
            if messages := v.get("messages"):
                logging.debug(f"got messages: {messages}")
                for m in messages:
                    if isinstance(m, ToolMessage):
                        info = get_tool_call_info(
                            context, tool_call_id=m.tool_call_id, index=None
                        )
                        if info:
                            remove_tool_call_info(context, tool_call_id=m.tool_call_id)
                            stream_msgs.append(
                                ToolCallResultEvent(
                                    delta=json.dumps(m.content),
                                    tool_call_id=m.tool_call_id,
                                    tool_call_name=m.name,
                                    tool_call_status=m.status,
                                )
                            )
    logging.info(f"stream_msgs: {stream_msgs}")
    return stream_msgs


def build_tool_description(tools: list[BaseTool]) -> str:
    tool_list = ""
    for tool in tools:
        tool_list += f"{tool.name}: {tool.description}\n"
    return tool_list

def create_agentic_bot(llm: ChatOpenAI):
    post_tool_caller_hook = get_post_tool_caller_hook(llm)
    tools_agent = create_react_agent(
        model=llm,
        tools=[get_real_time_weather, get_life_index],
        prompt=tool_call_system_prompt,
        name="tools_agent",
        pre_model_hook=pre_tool_caller_hook,
        post_model_hook=post_tool_caller_hook,
        state_schema=AgenticBotState
    )
    tool_list = build_tool_description([])
    planner_prompt = RunnableCallable(
        lambda state: [
                          {
                              "role": "system",
                              "content": planner_system_prompt.format(
                                  tool_list=tool_list,
                                  failed_trial_history=[
                                      {"failed_plan": reflect[0], "failed_reason": reflect[1]}
                                      for reflect in state.get("prev_reflect", [])
                                  ],
                              ),
                          }
                      ]
                      + state["messages"],
    )
    planer_agent = create_react_agent(
        model=llm,
        tools=[],
        prompt=planner_system_prompt,
        pre_model_hook=pre_planner_hook,
        post_model_hook=post_planner_hook,
        name="planner_agent",
        state_schema=AgenticBotState
    )
    summary_agent = create_react_agent(
        llm,
        [],
        prompt=summary_agent_system_prompt,
        name="summary_agent",
        state_schema=AgenticBotState
    )
    supervisor = create_supervisor(
        agents=[planer_agent, tools_agent, summary_agent],
        model=llm,
        tools=[],
        add_handoff_back_messages=True,
        output_mode="full_history",
        state_schema=AgenticBotState,
        prompt=supervisor_system_prompt
    ).compile()

    return supervisor
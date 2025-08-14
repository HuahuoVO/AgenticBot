import logging
import re

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, ToolMessage, SystemMessage, BaseMessage
from langchain_core.output_parsers import JsonOutputToolsParser, JsonOutputParser

from agent.State import AgenticBotState


def get_post_tool_caller_hook(model: BaseChatModel):
    def post_tool_caller_hook(state: AgenticBotState):
        messages = state["messages"]

        # async with aiofiles.open('tool_caller_log', 'w') as f:
        #     await f.write(str(messages))

        def summarize_key_variables(state: AgenticBotState) -> AgenticBotState:
            """
            LLM node to summarize key variables from the conversation history.
            """

            llm = model
            json_llm = llm.bind(response_format={"type": "json_object"})

            messages = state["messages"]
            msg_idx = len(messages) - 1
            for msg in reversed(messages):
                if (
                    isinstance(msg, ToolMessage)
                    and msg.name == "transfer_to_tools_agent"
                ):
                    # hand off message
                    break
                msg_idx -= 1
            else:
                raise ValueError("no hand off message found")

            # with open('full_msgs', 'w') as f:
            #     f.write(str(full_msgs))
            transfer_message: AIMessage = messages[msg_idx - 1]
            assert (
                isinstance(transfer_message, AIMessage)
                and len(transfer_message.tool_calls) == 1
            ), f"transfer message must be AIMessage with 1 tool call, got {transfer_message}"
            print(f"transfer message={transfer_message}")
            # build fake human message
            # call_tool_message = transfer_message.tool_calls[0]['args']
            # fake_human = HumanMessage(content=json.dumps(call_tool_message))
            empty_transfer = transfer_message

            empty_transfer.content = ""
            # 截取这两个之间的消息
            tool_agent_msgs = messages[msg_idx:]
            tool_agent_msgs = [empty_transfer] + tool_agent_msgs
            print(f"tool_agent_msgs={tool_agent_msgs}")
            # 构造LLM的输入提示
            # 这里的提示非常重要，它指导LLM如何总结关键变量
            prompt_messages = [
                SystemMessage(
                    content=f"You are an AI assistant tasked with identifying and summarizing key variables from a conversation history. These variables could be user intentions, specific entities (like location, dates), important parameters (like product names, product images, product brand, product IDs, etc.), or any information crucial for further processing. Note that only new variables are retained; variables existing in current available do not need to be saved again. Return the variables in a JSON format like: {{'variables': {{'var1': 'value1', 'var2': 'value2'}}}}\n curent available vars are: {state.get('available_vars', {})}"
                ),
                *tool_agent_msgs,
            ]

            parser = JsonOutputParser()

            var_extractor = json_llm | parser | (lambda x: x.get("variables", {}))
            print(f"prompt_messages={prompt_messages}")
            response = var_extractor.invoke(prompt_messages)
            avail_vars = state.get("available_vars", {})
            state["available_vars"] = {**avail_vars, **response}
            return state

        if (
            messages[-1].response_metadata.get("finish_reason") == "stop"
            and messages[-1].name == "tools_agent"
        ):
            # 转回去的时候再summary
            state = summarize_key_variables(state)

        # RePlan pattern
        re_plan_pattern = re.compile(r"<RePlanReason>(.*?)</RePlanReason>", re.DOTALL)
        fail_step_pattern = re.compile(r"<FailStep>(.*?)</FailStep>", re.DOTALL)
        fail_reason_pattern = re.compile(r"<FailReason>(.*?)</FailReason>", re.DOTALL)
        if isinstance(messages[-1], AIMessage):
            if messages[-1].content and re_plan_pattern.search(messages[-1].content):
                # 解析<RePlanReason>
                re_plan_reason = re_plan_pattern.search(messages[-1].content).group(1)
                fail_step = fail_step_pattern.search(re_plan_reason).group(1)
                fail_reason = fail_reason_pattern.search(re_plan_reason).group(1)
                # 记录反思
                prev_reflection = state.get("prev_reflect", [])
                prev_reflection.append((state["plan"], [fail_step, fail_reason]))
                state["prev_reflect"] = prev_reflection

        return state

    return post_tool_caller_hook


def pre_tool_caller_hook(state: AgenticBotState):
    full_msgs: list[BaseMessage] = state["messages"]
    # 只需要拿到supervisor交给自己的任务，忽略其他上下文，手动实现filter
    # 找到最新的，name是supervisor的AIMessage
    msg_idx = len(full_msgs) - 1
    for msg in reversed(full_msgs):
        if isinstance(msg, ToolMessage) and msg.name == "transfer_to_tools_agent":
            # hand off message
            break
        msg_idx -= 1
    else:
        raise ValueError("no hand off message found")

    # with open('full_msgs', 'w') as f:
    #     f.write(str(full_msgs))
    transfer_message: AIMessage = full_msgs[msg_idx - 1]
    assert (
        isinstance(transfer_message, AIMessage)
        and len(transfer_message.tool_calls) == 1
    ), f"transfer message must be AIMessage with 1 tool call, got {transfer_message}"

    # build fake human message
    # call_tool_message = transfer_message.tool_calls[0]['args']
    # fake_human = HumanMessage(content=json.dumps(call_tool_message))
    empty_transfer = transfer_message
    empty_transfer.content = ""  # state['plan']
    # 截取这两个之间的消息
    tool_agent_msgs = full_msgs[msg_idx:]
    tool_agent_msgs = [empty_transfer] + tool_agent_msgs

    return {"llm_input_messages": tool_agent_msgs}


def post_planner_hook(state: AgenticBotState):
    messages = state["messages"]
    print(f"state={state}")
    print(f"messages[-1]={messages[-1]}")
    print(f"isinstance(messages[-1])={isinstance(messages[-1],AIMessage)}")
    print(f"messages[-1].name={messages[-1].name}")
    plan_pattern = re.compile(r"<Plan>(.*?)</Plan>", re.DOTALL)
    if isinstance(messages[-1], AIMessage):

        assert messages[-1].name == "planner_agent"
        search_result = plan_pattern.search(messages[-1].content)
        # assert search_result is not None, "The given plan is not correctly formated in <Plan></Plan>"
        plan = ""
        if search_result is not None:
            plan = search_result.group(1)
        if False:
            interrupt_config = {
                "allow_accept": True,
                "allow_edit": True,
                "allow_respond": False,
            }
            request: HumanInterrupt = {
                "action_request": {"action": "Execute the plan", "args": plan},
                "config": interrupt_config,
                "description": "Please review the plan",
            }
            response = interrupt([request])[0]
            if response["type"] == "accept":
                pass
            # update tool call args
            elif response["type"] == "edit":
                new_plan = response["args"]["args"]
                plan = new_plan
            # respond to the LLM with user feedback
            else:
                raise ValueError(
                    f"Unsupported interrupt response type: {response['type']}"
                )
        # result = interrupt({
        #     "task": "Please review and edit the generated plan if necessary.",
        #     "plan": plan
        # })
        # if 'ok' in result:
        #     pass
        # else:
        #     plan = result
    state["plan"] = plan if plan != "" else state.get("plan", "")
    state["prev_reflect"] = []
    return state


def pre_planner_hook(state: AgenticBotState):
    # 相关信息都在system prompt里面，这里直接把交互信息等删除，减少上下文
    return {"llm_input_messages": {}}
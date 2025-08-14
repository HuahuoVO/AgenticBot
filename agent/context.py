def create_context():
    return {}

def get_tool_call_info(context, index, tool_call_id=None):
    return context.get(str(index), {})

def add_tool_call_info(context, index=None, tool_info=None):
    context[str(index)] = tool_info

def remove_tool_call_info(context, tool_call_id, index=None):
    if tool_call_id in context:
        if index is not None:
            context[tool_call_id].pop(index, None)
        else:
            context.pop(tool_call_id, None)
def set_final_message(context):
    context["final_message"] = "final_message"

def get_final_message(context):
    return context.get("final_message")

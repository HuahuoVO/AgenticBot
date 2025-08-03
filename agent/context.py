def create_context():
    return {}

def get_tool_call_info(context, tool_call_id, index=None):
    if tool_call_id not in context:
        context[tool_call_id] = {}
    if index is not None:
        context[tool_call_id][index] = {}
    return context[tool_call_id]

def add_tool_call_info(context, tool_call_id, index=None, info=None):
    tool_call_info = get_tool_call_info(context, tool_call_id, index)
    if info:
        tool_call_info.update(info)

def remove_tool_call_info(context, tool_call_id, index=None):
    if tool_call_id in context:
        if index is not None:
            context[tool_call_id].pop(index, None)
        else:
            context.pop(tool_call_id, None)
def set_final_message(context, final_message):
    context["final_message"] = final_message

def get_final_message(context):
    return context.get("final_message")

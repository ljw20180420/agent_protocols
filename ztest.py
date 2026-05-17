from acp import start_tool_call, text_block, tool_content, update_tool_call

start_update = start_tool_call("call-42", "Open file", kind="read", status="pending")
finish_update = update_tool_call(
    "call-42",
    status="completed",
    content=[tool_content(text_block("File opened."))],
)

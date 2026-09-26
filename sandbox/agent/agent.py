class Agent:
    def __init__(self):
        self.name = "AgentChain-Test-Agent"
        self.tools = {}
        self.permissions = {}

    def register_tool(self, name, tool):
        self.tools[name] = tool

    def set_permission(self, tool_name, allowed):
        self.permissions[tool_name] = allowed

    def can_use(self, tool_name):
        return self.permissions.get(tool_name, False)

    def execute_tool(self, tool_name, *args, **kwargs):

        if not self.can_use(tool_name):
            return {
                "status": "denied",
                "tool": tool_name,
                "message": "Permission denied"
            }

        if tool_name not in self.tools:
            return {
                "status": "error",
                "tool": tool_name,
                "message": "Tool not found"
            }

        result = self.tools[tool_name](*args, **kwargs)

        return {
            "status": "success",
            "tool": tool_name,
            "result": result
        }
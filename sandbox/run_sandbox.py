from agent.agent import Agent
from agent.state import AgentState

from tools.search_tool import search_tool
from tools.file_tool import file_tool
from tools.memory_tool import memory_tool


def main():

    print("=" * 50)
    print("AgentChain Security Sandbox")
    print("=" * 50)

    # Create agent
    agent = Agent()
    state = AgentState()

    # Register tools
    agent.register_tool("search", search_tool)
    agent.register_tool("file", file_tool)

    # Memory tool needs state
    agent.register_tool(
        "memory",
        lambda action, key=None, value=None:
            memory_tool(state, action, key, value)
    )

    # Initial permissions
    agent.set_permission("search", True)
    agent.set_permission("file", True)
    agent.set_permission("memory", True)

    print("\nAgent initialized")

    print("\nAvailable tools:")
    for tool in agent.tools:
        print(f"✓ {tool}")

    print("\nPermissions:")
    for tool, permission in agent.permissions.items():
        print(f"{tool}: {'ALLOWED' if permission else 'DENIED'}")

    # Test search
    print("\n--- Search Test ---")

    result = agent.execute_tool(
        "search",
        "cybersecurity"
    )

    print(result)

    # Test file
    print("\n--- File Test ---")

    result = agent.execute_tool(
        "file",
        "public.txt"
    )

    print(result)

    # Test memory
    print("\n--- Memory Test ---")

    result = agent.execute_tool(
        "memory",
        "write",
        "test_key",
        "hello"
    )

    print(result)

    result = agent.execute_tool(
        "memory",
        "read",
        "test_key"
    )

    print(result)

    print("\n" + "=" * 50)
    print("Sandbox ready")
    print("=" * 50)


if __name__ == "__main__":
    main()
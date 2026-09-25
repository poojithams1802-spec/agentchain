class AgentState:
    def __init__(self):
        self.memory = {}
        self.history = []
        self.current_user = "test_user"

    def add_history(self, action):
        self.history.append(action)

    def set_memory(self, key, value):
        self.memory[key] = value

    def get_memory(self, key):
        return self.memory.get(key)

    def get_state(self):
        return {
            "current_user": self.current_user,
            "memory": self.memory,
            "history": self.history
        }
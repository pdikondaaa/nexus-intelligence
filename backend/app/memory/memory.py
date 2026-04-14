# app/memory/memory.py

class ChatMemory:
    def __init__(self):
        self.store = {}

    def add(self, session_id, user, ai):
        if session_id not in self.store:
            self.store[session_id] = []
        self.store[session_id].append({"user": user, "ai": ai})

    def get(self, session_id):
        return self.store.get(session_id, [])
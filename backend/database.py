import json
import os

DB_FILE = "medicines.json"

class Database:
    def __init__(self):
        self.data = self._load()

    def _load(self):
        if not os.path.exists(DB_FILE):
            return {"medicines": [], "logs": []}
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    def load(self):
        self.data = self._load()
        return self.data

    def save(self):
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=4)

db = Database()

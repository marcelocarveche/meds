import json
import os
from typing import List, Dict

DB_FILE = "medicines.json"

class Database:
    def __init__(self):
        self.data = self._load()

    def _load(self):
        if not os.path.exists(DB_FILE):
            return {"medicines": [], "logs": []}
        with open(DB_FILE, "r") as f:
            return json.load(f)

    def save(self):
        with open(DB_FILE, "w") as f:
            json.dump(self.data, f, indent=4)

db = Database()

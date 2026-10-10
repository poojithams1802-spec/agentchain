
import os
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient

# Resolve backend/.env regardless of the directory used to start Uvicorn.
BACKEND_DIR = Path(__file__).resolve().parents[1]
ENV_FILE = BACKEND_DIR / ".env"

load_dotenv(dotenv_path=ENV_FILE, override=False)

MONGO_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "agentchain")

client = MongoClient(MONGO_URI)
db = client[MONGO_DB_NAME]

# Phase 3 multi-agent state persistence
db.agent_states


import os
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient

# Project root: E:\Projects\agentchain
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / ".env"

load_dotenv(dotenv_path=ENV_FILE, override=False)

MONGO_URI = os.getenv("MONGODB_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "agentchain")

if not MONGO_URI:
    raise RuntimeError(
        f"MONGODB_URI is missing. Check the environment file: {ENV_FILE}"
    )

client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=10000)
db = client[MONGO_DB_NAME]

# Phase 3 multi-agent state persistence
db.agent_states

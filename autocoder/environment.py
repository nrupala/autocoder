"""
AutoCoder Environment Configuration
=====================================
Persistent environment settings for AutoCoder.
"""

import os
from pathlib import Path

# Get working directory
WORK_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = WORK_DIR / "data"
CONFIG_DIR = WORK_DIR / "config"
MODELS_DIR = WORK_DIR / "models"

# Create directories
DATA_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# Database
DB_PATH = str(DATA_DIR / "autocoder.db")
DB_URL = f"sqlite:///{DB_PATH}"

# Cache settings
CACHE_DIR = DATA_DIR / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL = 3600  # 1 hour
CACHE_MAX_SIZE = 1000

# Logging
LOG_DIR = DATA_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "autocoder.log"
LOG_LEVEL = "INFO"

# Model settings
DEFAULT_MODEL = "template"
OLLAMA_URL = "http://localhost:11434"
LMSTUDIO_URL = "http://localhost:1234"

# Rate limiting
RATE_LIMIT_CALLS = 10
RATE_LIMIT_PERIOD = 60  # seconds

# Environment
ENV = os.getenv("AUTOCODER_ENV", "development")
DEBUG = ENV == "development"

# Serialization
SERIALIZATION_FORMAT = "json"  # json, pickle, msgpack

class Environment:
    """Persistent environment manager."""
    
    def __init__(self):
        self.work_dir = WORK_DIR
        self.data_dir = DATA_DIR
        self.config_dir = CONFIG_DIR
        self.models_dir = MODELS_DIR
        self.env = ENV
        self.debug = DEBUG
        
    def get_db_path(self) -> str:
        return DB_PATH
    
    def get_cache_dir(self) -> str:
        return str(CACHE_DIR)
    
    def get_log_file(self) -> str:
        return str(LOG_FILE)
    
    def is_production(self) -> bool:
        return ENV == "production"
    
    def is_development(self) -> bool:
        return ENV == "development"

# Global environment
env = Environment()
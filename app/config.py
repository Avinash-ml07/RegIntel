import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    PROJECT_NAME: str = "RegIntel Watcher Agent (Air-Gapped)"
    API_V1_STR: str = "/api/v1"
    LOG_LEVEL: str = "INFO"
    
    # Air-Gapped Local Dropbox Storage Configuration
    REGULATORY_DROPBOX: Path = Path("./regulatory_dropbox")
    
    # Local Offline Ollama Configuration
    LOCAL_OLLAMA_BASE_URL: str = "http://localhost:11434"
    LOCAL_OLLAMA_MODEL: str = "llama3"

settings = Settings()

# Bootstrap the local dropbox directory if it does not exist
os.makedirs(settings.REGULATORY_DROPBOX, exist_ok=True)
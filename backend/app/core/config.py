from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Interview Coach"
    app_env: str = "local"
    api_host: str = "127.0.0.1"
    api_port: int = 8000

    cors_origins: str = "http://localhost:4200,http://127.0.0.1:4200"
    cors_allow_origin_regex: str = r"http://(localhost|127\.0\.0\.1|172\.\d+\.\d+\.\d+):\d+"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "gpt-oss:20b"

    embedding_provider: str = "hashing"
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    reranker_provider: str = "heuristic"
    cross_encoder_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    vector_store: str = "inmemory"
    data_dir: Path = Field(default=Path("./data"))

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings_obj = Settings()
    settings_obj.data_dir.mkdir(parents=True, exist_ok=True)
    (settings_obj.data_dir / "uploads").mkdir(parents=True, exist_ok=True)
    (settings_obj.data_dir / "videos").mkdir(parents=True, exist_ok=True)
    return settings_obj


settings = get_settings()

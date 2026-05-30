from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    groq_timeout: int = 10
    react_max_iterations: int = 5
    react_timeout: int = 30

    database_url: str = "sqlite+aiosqlite:///:memory:"
    test_database_url: str = "sqlite+aiosqlite:///:memory:"

    cache_ttl: int = 3600
    max_upload_size: int = 10 * 1024 * 1024  # 10MB

    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]


settings = Settings()

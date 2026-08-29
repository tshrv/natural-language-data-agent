from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "SQL Agent"
    debug: bool = False

    # database settings
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str
    postgres_db_schema: str
    postgres_user_ro: str
    postgres_password_ro: str
    max_db_connections: int

    # llm
    groq_api_key: str
    model_name: str = "qwen/qwen3.6-27b"
    # qwen/qwen3.6-27b
    # groq/compound
    # openai/gpt-oss-20b

    # agent
    max_agent_iterations: int = 10
    cache_ttl_seconds: int = 3600
    plan_rows_warning: int = 100_000
    plan_cost_warning: int = 1_000_000

    @computed_field
    @property
    def db_url(self) -> str:
        """Raw driver connection string."""
        return f"postgresql://{self.postgres_user_ro}:{self.postgres_password_ro}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()

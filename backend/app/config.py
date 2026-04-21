from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./mni.db"
    NEWSAPI_KEY: str = ""
    MOCK_MODE: str = "auto"
    POLL_NEWS_SECONDS: int = 60
    POLL_MARKET_SECONDS: int = 60
    ALLOWED_ORIGINS: str = "http://localhost:5173"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

    @property
    def use_mock(self) -> bool:
        if self.MOCK_MODE == "on":
            return True
        if self.MOCK_MODE == "off":
            return False
        return not bool(self.NEWSAPI_KEY)


settings = Settings()

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./mni.db"
    REDIS_URL: str = ""
    NEWSAPI_KEY: str = ""
    MOCK_MODE: str = "auto"
    POLL_NEWS_SECONDS: int = 60
    POLL_MARKET_SECONDS: int = 60
    ALLOWED_ORIGINS: str = "http://localhost:5173"
    ALLOWED_ORIGIN_REGEX: str = ""
    JWT_SECRET: str = "dev-insecure-change-me"
    JWT_ALG: str = "HS256"
    JWT_EXPIRE_HOURS: int = 168

    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRICE_PRO: str = ""
    STRIPE_PRICE_PREMIUM: str = ""
    STRIPE_PRICE_TEAM: str = ""
    STRIPE_PRICE_API: str = ""
    BILLING_SUCCESS_URL: str = "http://localhost:5173/account?checkout=success"
    BILLING_CANCEL_URL: str = "http://localhost:5173/pricing?checkout=cancelled"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

    @property
    def stripe_enabled(self) -> bool:
        return bool(self.STRIPE_SECRET_KEY)

    def stripe_price_for(self, plan_key: str) -> str:
        return {
            "pro": self.STRIPE_PRICE_PRO,
            "premium": self.STRIPE_PRICE_PREMIUM,
            "team": self.STRIPE_PRICE_TEAM,
            "api": self.STRIPE_PRICE_API,
        }.get(plan_key, "")

    @property
    def use_mock(self) -> bool:
        if self.MOCK_MODE == "on":
            return True
        if self.MOCK_MODE == "off":
            return False
        return not bool(self.NEWSAPI_KEY)


settings = Settings()

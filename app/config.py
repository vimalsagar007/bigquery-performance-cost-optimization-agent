import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    GOOGLE_CLOUD_PROJECT: str = os.getenv("GOOGLE_CLOUD_PROJECT", "qwiklabs-gcp-02-63b2f55175ee")
    GOOGLE_CLOUD_LOCATION: str = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    GOOGLE_GENAI_USE_VERTEXAI: bool = True
    BQ_REGION: str = os.getenv("BQ_REGION", "US")
    BQ_ON_DEMAND_PRICE_PER_TB: float = float(os.getenv("BQ_ON_DEMAND_PRICE_PER_TB", "6.25"))
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()

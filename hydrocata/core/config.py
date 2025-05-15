from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuration settings for the HydroCata-A API."""

    app_name: str = "HydroCata-A API"
    api_version: str = "1.0.0"
    storage_type: str = "sql"  # Can be extended to 'database' later

    class Config:
        env_prefix = "HYDROCATA_"  # Prefix for environment variables
        case_sensitive = False


settings = Settings()

"""
Application configuration, loaded from environment variables.

This is the ONLY file that should read from os.environ / .env.
Every other module receives config as function arguments or via this
`settings` object - never reads the environment directly. That keeps
business logic testable without env-juggling.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./tiktok_engine.db"
    sql_echo: bool = False

    hermes_api_url: str = "http://localhost:8080"  
    hermes_api_key: str = ""

    scraper_headless: bool = True
    scraper_shortlist_size: int = 5
    scraper_min_commission_pct: float = 15.0
    scraper_min_stock: int = 50

    nvidia_api_key: str = ""
    nvidia_api_url: str = "https://integrate.api.nvidia.com/v1"
    nvidia_vision_model: str = "meta/llama-3.2-11b-vision-instruct"

    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    
    class Config:
        env_file = ".env"


settings = Settings()

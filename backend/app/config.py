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

    hermes_api_url: str = "http://localhost:8080"  # TODO: point at your Hermes Agent instance
    hermes_api_key: str = ""

    scraper_headless: bool = True

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()

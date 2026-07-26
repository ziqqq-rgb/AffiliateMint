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

    threads_user_id: str = ""
    threads_access_token: str = ""
    auto_publish_shopee_threads: bool = False
    
    nvidia_api_base: str = "https://integrate.api.nvidia.com/v1/chat/completions"
    nvidia_api_key: str = ""
    nvidia_model: str = "nvidia/nemotron-3-super-120b-a12b"

    gemini_api_base: str = "https://generativelanguage.googleapis.com/v1beta/models"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.6-flash"

    # Default: Anthropic-hosted Firecrawl. Point at a self-hosted instance
    # instead by setting FIRECRAWL_API_BASE=http://localhost:3002/v1 in
    # .env (see infra/firecrawl/ setup below) - firecrawl_client.py reads
    # this, no code change needed either way.
    firecrawl_api_base: str = "https://api.firecrawl.dev/v1"
    firecrawl_api_key: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore" 


settings = Settings()
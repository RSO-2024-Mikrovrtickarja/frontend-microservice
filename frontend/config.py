from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    users_host: str
    users_port: int
    
    photo_storage_host: str
    photo_storage_port: int

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

config = Config()
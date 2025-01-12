from pydantic_settings import BaseSettings, SettingsConfigDict
import os

DOTENV = os.path.join(os.path.dirname(__file__), "..", ".env")

class Config(BaseSettings):    
    users_host: str
    users_port: int
    
    photo_storage_host: str
    photo_storage_port: int
    
    upscale_api_key: str

    model_config = SettingsConfigDict(env_file=DOTENV, env_file_encoding="utf-8")

config = Config()

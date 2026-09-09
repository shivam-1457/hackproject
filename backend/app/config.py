from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    frontend_url: str = "http://127.0.0.1:5500"
    email_host: str = "smtp.gmail.com"
    email_port: int = 587
    email_username: str = "kisan2consumerhelp@gmail.com"
    email_password: str = ""
    email_from: str = "kisan2consumerhelp@gmail.com"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()

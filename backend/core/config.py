from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Cấu hình chung của dự án
    PROJECT_NAME: str = "CV Mentor"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Web Server config
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    # Google API Key
    GOOGLE_API_KEY: str
    
    # JWT Authentication
    JWT_SECRET: str
    JWT_ALGORITHM: str
    JWT_EXPIRE_HOURS: int

    # Database
    DATABASE_URL: str

    #ollama
    OLLAMA_HOST: str = "https://ollama.com"
    OLLAMA_API_KEY: str
    OLLAMA_MODEL: str = "gpt-oss:120b"
    
    # Groq Cloud API (để chạy Whisper STT miễn phí tốc độ cao)
    GROQ_API_KEY: str = ""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
settings = Settings()

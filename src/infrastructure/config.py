from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr, computed_field

class Settings(BaseSettings):
    # Binance Config
    BINANCE_API_KEY: str
    BINANCE_SECRET_KEY: SecretStr | None = None
    BINANCE_PUBLIC_KEY_PATH: str
    BINANCE_PRIVATE_KEY_PATH: str

    # Database Config (Sin valores hardcodeados)
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    DB_HOST: str
    DB_PORT: str

    # Agent Config
    LOG_LEVEL: str = "INFO" # Valor por defecto razonable

    @computed_field
    @property
    def DATABASE_URL(self) -> str:
    # Esta URL será: postgresql+asyncpg://admin:crypto_secret@timescaledb:5432/aurca
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.POSTGRES_DB}"

    # Configuración de Pydantic para leer el archivo .env
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore" # Ignora variables extra en el .env que no usemos aquí
    )

settings = Settings()
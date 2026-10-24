import os

from pydantic_settings import BaseSettings, SettingsConfigDict

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_DEFAULT_DB_PATH = os.path.join(_BASE_DIR, "fundguard.db")


class Settings(BaseSettings):
    app_name: str = "Omega FundGuard"
    app_env: str = "development"
    database_url: str = f"sqlite:///{_DEFAULT_DB_PATH}"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    settlement_mode: str = "simulated"
    allow_stellar_testnet: bool = True
    allow_stellar_mainnet: bool = False
    stellar_network_passphrase: str = "Test SDF Network ; September 2015"
    stellar_horizon_url: str = "https://horizon-testnet.stellar.org"
    stellar_source_secret_key: str | None = None
    default_organization_id: str = "org-fundguard-global"
    default_organization_name: str = "FundGuard Global Organization"
    near_intents_simulation_rate: float = 0.085  # Simulated XLM to NEAR exchange rate
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()

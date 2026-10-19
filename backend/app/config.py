from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Omega FundGuard"
    app_env: str = "development"
    database_url: str = "sqlite:///./fundguard.db"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    settlement_mode: str = "simulated"
    allow_stellar_testnet: bool = True
    allow_stellar_mainnet: bool = False
    stellar_network_passphrase: str = "Test SDF Network ; September 2015"
    stellar_horizon_url: str = "https://horizon-testnet.stellar.org"
    stellar_source_secret_key: str | None = None
    default_organization_id: str = "org-basix-global"
    default_organization_name: str = "BASIX Market Hackathons"
    near_intents_simulation_rate: float = 0.085  # Simulated XLM to NEAR exchange rate
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()

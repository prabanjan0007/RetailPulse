from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    database: str = os.getenv("POSTGRES_DB", "retailpulse")
    user: str = os.getenv("POSTGRES_USER", "retailpulse")
    password: str = os.getenv("POSTGRES_PASSWORD", "retailpulse")
    host: str = os.getenv("POSTGRES_HOST", "localhost")
    port: int = int(os.getenv("POSTGRES_PORT", "5432"))

    @property
    def database_url(self) -> str:
        return (
            f"postgresql://{self.user}:{self.password}@{self.host}:"
            f"{self.port}/{self.database}"
        )


settings = Settings()


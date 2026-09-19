from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path


class ConfigurationError(ValueError):
    pass


@dataclass(frozen=True)
class DoctorSettings:
    repository_root: Path
    queue_database: Path
    security_database: Path
    client_secrets: dict[str, str]
    requests_per_minute: int = 60
    burst: int = 20

    @classmethod
    def from_environment(cls, environment: dict[str, str] | None = None) -> "DoctorSettings":
        env = environment or dict(os.environ)
        required = [
            "SIMS_DOCTOR_QUEUE_DB",
            "SIMS_DOCTOR_SECURITY_DB",
            "SIMS_DOCTOR_CLIENT_SECRETS_JSON",
        ]
        missing = [name for name in required if not env.get(name)]
        if missing:
            raise ConfigurationError(
                "Missing required environment variables: " + ", ".join(missing)
            )
        try:
            secrets = json.loads(env["SIMS_DOCTOR_CLIENT_SECRETS_JSON"])
        except json.JSONDecodeError as exc:
            raise ConfigurationError(
                "SIMS_DOCTOR_CLIENT_SECRETS_JSON must be valid JSON"
            ) from exc
        if not isinstance(secrets, dict) or not secrets:
            raise ConfigurationError("At least one API client secret is required")
        if any(not isinstance(key, str) or not isinstance(value, str) for key, value in secrets.items()):
            raise ConfigurationError("Client IDs and secrets must be strings")
        if any(len(value) < 16 for value in secrets.values()):
            raise ConfigurationError("Each client secret must be at least 16 characters")
        if any(value.lower() in {"secret", "changeme", "password"} for value in secrets.values()):
            raise ConfigurationError("Default or placeholder secrets are forbidden")

        root = Path(env.get("SIMS_DOCTOR_REPOSITORY_ROOT", ".")).resolve()
        return cls(
            repository_root=root,
            queue_database=Path(env["SIMS_DOCTOR_QUEUE_DB"]).resolve(),
            security_database=Path(env["SIMS_DOCTOR_SECURITY_DB"]).resolve(),
            client_secrets=secrets,
            requests_per_minute=int(env.get("SIMS_DOCTOR_RATE_LIMIT_PER_MINUTE", "60")),
            burst=int(env.get("SIMS_DOCTOR_RATE_LIMIT_BURST", "20")),
        )

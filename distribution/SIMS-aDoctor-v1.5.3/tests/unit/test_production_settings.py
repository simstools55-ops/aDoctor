import json
import pytest

from src.doctor.config import DoctorSettings, ConfigurationError


def environment(tmp_path):
    return {
        "SIMS_DOCTOR_REPOSITORY_ROOT": str(tmp_path),
        "SIMS_DOCTOR_QUEUE_DB": str(tmp_path / "queue.db"),
        "SIMS_DOCTOR_SECURITY_DB": str(tmp_path / "security.db"),
        "SIMS_DOCTOR_CLIENT_SECRETS_JSON": json.dumps(
            {"sbm": "0123456789abcdef0123456789abcdef"}
        ),
    }


def test_loads_valid_environment(tmp_path):
    settings = DoctorSettings.from_environment(environment(tmp_path))
    assert settings.client_secrets["sbm"].startswith("0123")
    assert settings.queue_database.name == "queue.db"


def test_rejects_missing_environment(tmp_path):
    with pytest.raises(ConfigurationError, match="Missing required"):
        DoctorSettings.from_environment({})


def test_rejects_placeholder_secret(tmp_path):
    env = environment(tmp_path)
    env["SIMS_DOCTOR_CLIENT_SECRETS_JSON"] = json.dumps({"sbm": "changeme"})
    with pytest.raises(ConfigurationError):
        DoctorSettings.from_environment(env)

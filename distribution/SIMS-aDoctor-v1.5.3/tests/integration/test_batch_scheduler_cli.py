import json
from pathlib import Path

from src.doctor.cli.batch_scheduler import main

ROOT = Path(__file__).resolve().parents[2]


def test_cli_enqueue_run_and_status(tmp_path, capsys):
    database = tmp_path / "queue.db"
    log = tmp_path / "operations.jsonl"
    request = ROOT / "tests/fixtures/batch/batch_request.json"
    common = ["--database", str(database), "--repository-root", str(ROOT), "--log", str(log)]
    assert main(common + ["enqueue", "--request", str(request)]) == 0
    enqueued = json.loads(capsys.readouterr().out)
    queue_id = enqueued["queue_record_id"]

    code = main(common + [
        "run", "--queue-id", queue_id,
        "--executor", "tests.fixtures.batch.executor_module:execute",
        "--owner", "cli-test",
    ])
    assert code == 0
    result = json.loads(capsys.readouterr().out)
    assert result[0]["status"] == "COMPLETED"

    assert main(common + ["status", "--queue-id", queue_id]) == 0
    status = json.loads(capsys.readouterr().out)
    assert status["progress"]["completed"] == 2
    assert log.read_text(encoding="utf-8").count("CLI_BATCH") >= 2

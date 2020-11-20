from pathlib import Path

from autopr import workdir
from test.test_utils import run_cli, simple_test_config, simple_test_database


def test_create_files(tmp_path):
    testkey = Path(tmp_path) / "testkey"
    testkey.touch()

    wd = workdir.WorkDir(Path(tmp_path))
    run_cli(wd, ["init", "--api-key", "test", "--ssh-key-file", f"{testkey}"])

    assert wd.config_file.is_file()
    assert wd.database_file.is_file()
    assert wd.repos_dir.is_dir()


def test_no_override_files(tmp_path):
    wd = workdir.WorkDir(Path(tmp_path))

    testkey = Path(tmp_path) / "testkey"
    testkey.touch()

    result = run_cli(
        wd,
        ["init", "--api-key", "not-written", "--ssh-key-file", f"{testkey}"],
        cfg=simple_test_config(),
        db=simple_test_database(),
    )

    cfg = workdir.read_config(wd)
    db = workdir.read_database(wd)

    assert cfg.credentials.api_key == "test"
    assert db.repositories[0].name == "test"
    assert "config file exists" in result.output
    assert "database file exists" in result.output

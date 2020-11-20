from pathlib import Path

from click.testing import CliRunner

from autopr import cli, workdir, config, database


def test_create_files(tmp_path):
    testkey = Path(tmp_path) / "testkey"
    testkey.touch()

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["-w", tmp_path, "init", "--api-key", "test", "--ssh-key-file", f"{testkey}"],
    )
    assert result.exit_code == 0

    wd = workdir.WorkDir(Path(tmp_path))
    assert wd.config_file.exists() and wd.config_file.is_file()
    assert wd.database_file.exists() and wd.database_file.is_file()
    assert wd.repos_dir.exists() and wd.repos_dir.is_dir()


def test_no_override_files(tmp_path):
    wd = workdir.WorkDir(Path(tmp_path))

    credentials = config.Credentials(api_key="test", ssh_key_file="test")
    pr = config.PrTemplate()
    cfg = config.Config(credentials=credentials, pr=pr)

    repo = database.Repository(
        owner="test", name="test", ssh_url="test@testytest.com", default_branch="master"
    )
    db = database.Database(repositories=[repo])

    workdir.write_config(wd, cfg)
    workdir.write_database(wd, db)

    testkey = Path(tmp_path) / "testkey"
    testkey.touch()

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "-w",
            tmp_path,
            "init",
            "--api-key",
            "not-written",
            "--ssh-key-file",
            f"{testkey}",
        ],
    )
    assert result.exit_code == 0

    cfg = workdir.read_config(wd)
    db = workdir.read_database(wd)

    assert cfg.credentials.api_key == "test"
    assert db.repositories[0].name == "test"
    assert "config file exists" in result.output
    assert "database file exists" in result.output

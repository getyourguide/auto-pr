import os
from pathlib import Path

import pytest

from autopr import config, workdir
from autopr.util import CliException


def test_workdir_custom_repos_dir_via_constructor(tmp_path):
    """Test WorkDir with custom_repos_dir set via constructor"""
    custom_dir = Path(tmp_path) / "custom-repos"
    custom_dir.mkdir()

    wd = workdir.WorkDir(Path(tmp_path), custom_repos_dir=custom_dir)
    assert wd.repos_dir == custom_dir


def test_workdir_custom_repos_dir_via_config(tmp_path):
    """Test WorkDir with custom_repos_dir set via config file"""
    custom_dir = Path(tmp_path) / "custom-repos"
    custom_dir.mkdir()

    # Create a config with custom_repos_dir
    wd = workdir.WorkDir(Path(tmp_path))
    credentials = config.Credentials(api_key="test", ssh_key_file="test_key")
    pr = config.PrTemplate()
    cfg = config.Config(
        credentials=credentials, pr=pr, custom_repos_dir=str(custom_dir)
    )
    workdir.write_config(wd, cfg)

    # Read it back and verify repos_dir
    assert wd.repos_dir == custom_dir


def test_workdir_priority_cli_over_config(tmp_path):
    """Test that CLI option takes precedence over config file"""
    cli_custom_dir = Path(tmp_path) / "cli-repos"
    cli_custom_dir.mkdir()
    config_custom_dir = Path(tmp_path) / "config-repos"
    config_custom_dir.mkdir()

    # Create a config with custom_repos_dir
    wd_setup = workdir.WorkDir(Path(tmp_path))
    credentials = config.Credentials(api_key="test", ssh_key_file="test_key")
    pr = config.PrTemplate()
    cfg = config.Config(
        credentials=credentials, pr=pr, custom_repos_dir=str(config_custom_dir)
    )
    workdir.write_config(wd_setup, cfg)

    # Create WorkDir with CLI custom_repos_dir
    wd = workdir.WorkDir(Path(tmp_path), custom_repos_dir=cli_custom_dir)
    assert wd.repos_dir == cli_custom_dir
    assert wd.repos_dir != config_custom_dir


def test_workdir_default_behavior(tmp_path):
    """Test default behavior when no custom_repos_dir is specified"""
    wd = workdir.WorkDir(Path(tmp_path))
    expected_default = Path(tmp_path) / "repos"
    assert wd.repos_dir == expected_default


def test_init_validates_custom_repos_dir_exists(tmp_path):
    """Test init fails with clear error when custom repos dir doesn't exist"""
    nonexistent_dir = Path(tmp_path) / "nonexistent-repos"

    wd = workdir.WorkDir(Path(tmp_path), custom_repos_dir=nonexistent_dir)
    credentials = config.Credentials(api_key="test", ssh_key_file="test_key")

    with pytest.raises(CliException) as exc_info:
        workdir.init(wd, credentials)

    assert str(nonexistent_dir) in str(exc_info.value)
    assert "does not exist" in str(exc_info.value)


def test_init_success_with_existing_custom_repos_dir(tmp_path):
    """Test init succeeds when custom repos dir exists"""
    custom_dir = Path(tmp_path) / "existing-repos"
    custom_dir.mkdir()

    test_key = Path(tmp_path) / "test_key"
    test_key.touch()

    wd = workdir.WorkDir(Path(tmp_path), custom_repos_dir=custom_dir)
    credentials = config.Credentials(api_key="test", ssh_key_file=str(test_key))

    # Should not raise
    workdir.init(wd, credentials)

    # Verify custom dir still exists and was not modified
    assert custom_dir.exists()
    assert custom_dir.is_dir()


def test_init_creates_default_repos_dir(tmp_path):
    """Test init creates default repos dir when no custom dir specified"""
    test_key = Path(tmp_path) / "test_key"
    test_key.touch()

    wd = workdir.WorkDir(Path(tmp_path))
    credentials = config.Credentials(api_key="test", ssh_key_file=str(test_key))

    default_repos_dir = Path(tmp_path) / "repos"
    assert not default_repos_dir.exists()

    workdir.init(wd, credentials)

    # Verify default repos dir was created
    assert default_repos_dir.exists()
    assert default_repos_dir.is_dir()


def test_config_custom_repos_dir_env_var_expansion(tmp_path):
    """Test environment variable expansion in custom_repos_dir"""
    # Set environment variable
    custom_repos_base = Path(tmp_path) / "my-repos"
    custom_repos_base.mkdir()
    os.environ["TEST_CUSTOM_REPOS_DIR"] = str(custom_repos_base)

    try:
        # Create config with env var
        wd = workdir.WorkDir(Path(tmp_path))
        credentials = config.Credentials(api_key="test", ssh_key_file="test_key")
        pr = config.PrTemplate()
        cfg = config.Config(
            credentials=credentials,
            pr=pr,
            custom_repos_dir="${TEST_CUSTOM_REPOS_DIR}",
        )
        workdir.write_config(wd, cfg)

        # Read it back and verify expansion happened
        loaded_cfg = workdir.read_config(wd)
        assert loaded_cfg.custom_repos_dir == str(custom_repos_base)
    finally:
        del os.environ["TEST_CUSTOM_REPOS_DIR"]


def test_get_function_with_custom_repos_dir(tmp_path):
    """Test workdir.get() function with custom_repos_dir parameter"""
    custom_dir = Path(tmp_path) / "custom-repos"
    custom_dir.mkdir()

    wd = workdir.get(str(tmp_path), custom_repos_dir=custom_dir)
    assert wd.repos_dir == custom_dir


def test_get_function_without_custom_repos_dir(tmp_path):
    """Test workdir.get() function without custom_repos_dir parameter"""
    wd = workdir.get(str(tmp_path))
    expected_default = Path(tmp_path) / "repos"
    assert wd.repos_dir == expected_default


def test_init_with_custom_repos_dir_in_config(tmp_path):
    """Test init with custom_repos_dir specified in config file"""
    custom_dir = Path(tmp_path) / "custom-repos"
    custom_dir.mkdir()

    test_key = Path(tmp_path) / "test_key"
    test_key.touch()

    # First, create config with custom_repos_dir
    wd_setup = workdir.WorkDir(Path(tmp_path))
    credentials = config.Credentials(api_key="test", ssh_key_file=str(test_key))
    pr = config.PrTemplate()
    cfg = config.Config(
        credentials=credentials, pr=pr, custom_repos_dir=str(custom_dir)
    )
    workdir.write_config(wd_setup, cfg)

    # Now create a fresh WorkDir and init (simulating re-init)
    wd = workdir.WorkDir(Path(tmp_path))

    # Should not raise since custom_dir exists
    workdir.init(wd, credentials)

    # Verify repos_dir points to custom dir
    assert wd.repos_dir == custom_dir


def test_init_fails_with_nonexistent_custom_repos_dir_in_config(tmp_path):
    """Test init fails when custom_repos_dir in config doesn't exist"""
    nonexistent_dir = Path(tmp_path) / "nonexistent-repos"

    test_key = Path(tmp_path) / "test_key"
    test_key.touch()

    # Create config with nonexistent custom_repos_dir
    wd_setup = workdir.WorkDir(Path(tmp_path))
    credentials = config.Credentials(api_key="test", ssh_key_file=str(test_key))
    pr = config.PrTemplate()
    cfg = config.Config(
        credentials=credentials, pr=pr, custom_repos_dir=str(nonexistent_dir)
    )
    workdir.write_config(wd_setup, cfg)

    # Try to init - should fail
    wd = workdir.WorkDir(Path(tmp_path))
    with pytest.raises(CliException) as exc_info:
        workdir.init(wd, credentials)

    assert str(nonexistent_dir) in str(exc_info.value)
    assert "does not exist" in str(exc_info.value)

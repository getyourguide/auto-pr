import json
from pathlib import Path

import yaml
from marshmallow import ValidationError

from autopr import config, database
from autopr.util import CliException, warning

CONFIG_FILE_NAME = "config.yaml"
DB_FILE_NAME = "db.json"
REPOS_DIR_NAME = "repos"


class WorkDir:
    location: Path

    def __init__(self, location: Path):
        self.location = location

    @property
    def config_file(self) -> Path:
        return self.location / CONFIG_FILE_NAME

    @property
    def database_file(self) -> Path:
        return self.location / DB_FILE_NAME

    @property
    def repos_dir(self) -> Path:
        return self.location / REPOS_DIR_NAME


def init(wd: WorkDir, credentials: config.Credentials):
    # create work dir and repos dir
    wd.repos_dir.mkdir(parents=True, exist_ok=True)

    # create default config
    if not wd.config_file.exists():
        pr = config.PrTemplate()
        cfg = config.Config(credentials=credentials, pr=pr)
        write_config(wd, cfg)
    else:
        warning("config file exists - not overriding")

    # create empty database
    if not wd.database_file.exists():
        db = database.Database()
        write_database(wd, db)
    else:
        warning("database file exists - not overriding")


def write_config(wd: WorkDir, cfg: config.Config):
    # load config file
    try:
        data = config.CONFIG_SCHEMA.dump(cfg)
        with open(wd.config_file, "w") as config_file:
            yaml.dump(data, config_file, default_flow_style=False)
    except IOError as e:
        raise CliException(f"Failed to write config file: {e}")


def read_config(wd: WorkDir) -> config.Config:
    # load config file
    try:
        with open(wd.config_file) as config_file:
            config_dict = yaml.safe_load(config_file)
    except IOError as e:
        raise CliException(f"Failed to read config file: {e}")
    except yaml.YAMLError as e:
        raise CliException(f"Failed to parse config: {e}")

    # parse config data
    try:
        return config.CONFIG_SCHEMA.load(config_dict)
    except ValidationError as err:
        raise CliException(f"Failed to deserialize config: {err.messages}")


def write_database(wd: WorkDir, db: database.Database):
    # load database file
    try:
        data = database.DATABASE_SCHEMA.dump(db)
        with open(wd.database_file, "w") as database_file:
            json.dump(data, database_file, indent=4, sort_keys=True)
    except IOError as e:
        raise CliException(f"Failed to write database file: {e}")


def read_database(wd: WorkDir) -> database.Database:
    if not wd.database_file.exists():
        db = database.Database()
        return db

    # load database file
    try:
        with open(wd.database_file) as database_file:
            database_dict = json.load(database_file)
    except IOError as e:
        raise CliException(f"Failed to read database file: {e}")
    except json.JSONDecodeError as e:
        raise CliException(f"Failed to parse database: {e}")

    # parse database data
    try:
        return database.DATABASE_SCHEMA.load(database_dict)
    except ValidationError as err:
        raise CliException(f"Failed to deserialize database: {err.messages}")


def get(wd_path: str) -> WorkDir:
    if wd_path:
        workdir_path = Path(wd_path)
    else:
        workdir_path = Path.cwd()

    return WorkDir(workdir_path)

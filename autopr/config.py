import os
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import marshmallow_dataclass
from marshmallow import Schema, fields, post_load

DEFAULT_PR_TITLE = "Automatically generated PR"
DEFAULT_PR_MESSAGE = "Automatically generated commit"
DEFAULT_PR_BODY = "This is an automatically generated PR"
DEFAULT_PR_BRANCH = "autopr"

FILTER_MODE_ADD = "add"
FILTER_MODE_REMOVE = "remove"

FILTER_VISIBILITY_PUBLIC = "public"
FILTER_VISIBILITY_PRIVATE = "private"


def expand_env_vars(value: str) -> str:
    """
    Expand environment variables in a string.
    Supports ${VAR_NAME} syntax.

    Args:
        value: String that may contain ${VAR_NAME} patterns

    Returns:
        String with environment variables expanded

    Raises:
        ValueError: If referenced environment variable is not set
    """

    def replacer(match):
        var_name = match.group(1)
        env_value = os.getenv(var_name)
        if env_value is None:
            raise ValueError(f"Environment variable '{var_name}' is not set")
        return env_value

    # Match ${VAR_NAME} pattern
    return re.sub(r"\$\{([^}]+)\}", replacer, value)


@dataclass
class Credentials:
    api_key: str
    ssh_key_file: str


class CredentialsSchema(Schema):
    api_key = fields.Str(required=True)
    ssh_key_file = fields.Str(required=True)

    @post_load
    def expand_credentials_env_vars(
        self, data: Dict[str, Any], **kwargs: Any
    ) -> Credentials:
        """Expand environment variables in credential fields after loading."""
        if "api_key" in data and isinstance(data["api_key"], str):
            data["api_key"] = expand_env_vars(data["api_key"])
        if "ssh_key_file" in data and isinstance(data["ssh_key_file"], str):
            data["ssh_key_file"] = expand_env_vars(data["ssh_key_file"])
        return Credentials(**data)


CREDENTIALS_SCHEMA = CredentialsSchema()


@dataclass
class PrTemplate:
    title: str = DEFAULT_PR_TITLE
    message: str = DEFAULT_PR_MESSAGE
    branch: str = DEFAULT_PR_BRANCH
    body: str = DEFAULT_PR_BODY
    draft: bool = False


PR_TEMPLATE_SCHEMA = marshmallow_dataclass.class_schema(PrTemplate)()


@dataclass
class Filter:
    mode: str  # either 'add' or 'remove'
    public: Optional[bool] = None  # maps to the visibility of the repo
    archived: Optional[bool] = None
    match_name: Optional[
        List[str]
    ] = None  # a list of regex that are applied to the names, must match one
    match_owner: Optional[
        str
    ] = None  # a regex that is applied to the owners, must match one


FILTERS_SCHEMA = marshmallow_dataclass.class_schema(Filter)()


@dataclass
class Config:
    credentials: Credentials
    pr: PrTemplate
    repositories: List[Filter] = field(default_factory=list)  # is equal to assigning []
    update_command: List[str] = field(default_factory=list)
    custom_repos_dir: Optional[str] = None


class ConfigSchema(Schema):
    credentials = fields.Nested(CredentialsSchema, required=True)
    pr = fields.Nested(PR_TEMPLATE_SCHEMA, required=True)
    repositories = fields.List(fields.Nested(FILTERS_SCHEMA), load_default=list)
    update_command = fields.List(fields.Str(), load_default=list)
    custom_repos_dir = fields.Str(required=False, allow_none=True)

    @post_load
    def expand_config_env_vars(self, data: Dict[str, Any], **kwargs: Any) -> Config:
        """Expand environment variables in custom_repos_dir after loading."""
        if "custom_repos_dir" in data and data["custom_repos_dir"] is not None:
            data["custom_repos_dir"] = expand_env_vars(data["custom_repos_dir"])
        return Config(**data)


CONFIG_SCHEMA = ConfigSchema()

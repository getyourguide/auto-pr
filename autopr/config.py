from dataclasses import dataclass, field
from typing import List, Optional

import marshmallow_dataclass

DEFAULT_PR_TITLE = "Automatically generated PR"
DEFAULT_PR_MESSAGE = "Automatically generated commit"
DEFAULT_PR_BODY = "This is an automatically generated PR"
DEFAULT_PR_BRANCH = "autopr"

FILTER_MODE_ADD = "add"
FILTER_MODE_REMOVE = "remove"

FILTER_VISIBILITY_PUBLIC = "public"
FILTER_VISIBILITY_PRIVATE = "private"


@dataclass
class Credentials:
    api_key: str
    ssh_key_file: str


CREDENTIALS_SCHEMA = marshmallow_dataclass.class_schema(Credentials)()


@dataclass
class PrTemplate:
    title: str = DEFAULT_PR_TITLE
    message: str = DEFAULT_PR_MESSAGE
    branch: str = DEFAULT_PR_BRANCH
    body: str = DEFAULT_PR_BODY


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


CONFIG_SCHEMA = marshmallow_dataclass.class_schema(Config)()

from dataclasses import dataclass, field
from typing import List, Optional

from marshmallow import post_load
from marshmallow_annotations import AnnotationSchema


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


class CredentialsSchema(AnnotationSchema):
    class Meta:
        target = Credentials
        register_as_scheme = True

    @post_load
    def build(self, data, **kwargs):
        return Credentials(**data)


@dataclass
class PrTemplate:
    title: str = DEFAULT_PR_TITLE
    message: str = DEFAULT_PR_MESSAGE
    branch: str = DEFAULT_PR_BRANCH
    body: str = DEFAULT_PR_BODY


class PrTemplateSchema(AnnotationSchema):
    class Meta:
        target = PrTemplate
        register_as_scheme = True

    @post_load
    def build(self, data, **kwargs):
        return PrTemplate(**data)


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


class FilterSchema(AnnotationSchema):
    class Meta:
        target = Filter
        register_as_scheme = True

    @post_load
    def build(self, data, **kwargs):
        return Filter(**data)


@dataclass
class Config:
    credentials: Credentials
    pr: PrTemplate
    repositories: List[Filter] = field(default_factory=list)  # is equal to assigning []
    update_command: List[str] = field(default_factory=list)


class ConfigSchema(AnnotationSchema):
    class Meta:
        target = Config
        register_as_scheme = True

    @post_load
    def build(self, data, **kwargs):
        return Config(**data)

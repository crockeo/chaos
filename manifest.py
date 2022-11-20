from __future__ import annotations

from enum import Enum
from dataclasses import dataclass
from typing import Any

import yaml


# TODO: do some validation here and raise better errors
# also check that we're returning the right types
# see: type introspection helpers
# https://docs.python.org/3/library/typing.html#introspection-helpers


class Language(Enum):
    PYTHON_3_10 = ("python", (3, 10))
    PYTHON_3_11 = ("python", (3, 11))

    def formatted_version(self) -> str:
        _, version = self.value
        return ".".join(str(part) for part in version)

    def toolchain_name(self) -> str:
        language_id, _ = self.value
        formatted_version = self.formatted_version()
        formatted_version = formatted_version.replace(".", "_")
        return f"{language_id}{formatted_version}"

    def format(self) -> str:
        language, _ = self.value
        return f"{language}{self.formatted_version()}"

    @staticmethod
    def from_str(raw: str) -> Language:
        language_map = {}
        for case in Language:
            language_map[case.format()] = case
        return language_map[raw]


@dataclass
class Endpoint:
    name: str

    @staticmethod
    def from_dict(raw_endpoint: dict[str, Any]) -> Endpoint:
        return Endpoint(name=raw_endpoint["name"])


@dataclass
class Group:
    name: str
    language: Language
    filename: str
    endpoints: list[Endpoint]
    dependencies: str

    @staticmethod
    def from_dict(raw_group: dict[str, Any]) -> Group:
        return Group(
            name=raw_group["name"],
            language=Language.from_str(raw_group["language"]),
            filename=raw_group["filename"],
            endpoints=[
                Endpoint.from_dict(raw_endpoint)
                for raw_endpoint in raw_group["endpoints"]
            ],
            dependencies=raw_group["dependencies"],
        )


@dataclass
class Manifest:
    groups: list[Group]

    @staticmethod
    def from_dict(raw_manifest: dict[str, Any]) -> Manifest:
        return Manifest(
            groups=[
                Group.from_dict(raw_group)
                for raw_group in raw_manifest["groups"]
            ],
        )

    @staticmethod
    def load(path: str) -> Manifest:
        with open(path) as f:
            raw_manifest = yaml.full_load(f.read())
        return Manifest.from_dict(raw_manifest)

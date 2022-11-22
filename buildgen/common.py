from __future__ import annotations

from abc import ABC
from abc import abstractmethod

from manifest import Group
from manifest import Language


HTTP_ARCHIVE = """\
load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")
"""


def filename_as_target(filename: str) -> str:
    directory, _, filename = filename.rpartition("/")
    if not filename:
        return f"//:{directory}"
    return f"//{directory}:{filename}"


def get_toolchain_name(language: Language) -> str:
    formatted_version = language.formatted_version()
    formatted_version = formatted_version.replace(".", "_")
    return f"{language.id}{formatted_version}"


class BuildGenerator(ABC):
    @abstractmethod
    def generate_repository_rules(self) -> str:
        pass

    @abstractmethod
    def generate_toolchain(self, language: Language) -> str:
        pass

    @abstractmethod
    def generate_build_rules(self) -> str:
        pass

    @abstractmethod
    def generate_target(self, group: Group) -> str:
        pass

    @abstractmethod
    def generate_server_target(self, language: Language, groups: list[Group]) -> str:
        pass

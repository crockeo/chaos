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
        """\
        Loads the set of repository rules which are necessary
        to build projects in a particular language.
        E.g. rules_go or rules_python.
        """
        pass

    @abstractmethod
    def generate_toolchain(self, language: Language) -> str:
        """\
        Generates a particular toolchain for the target language.
        This parameterized by the actual toolchain (e.g. clang vs. gcc)
        as well as the major version (e.g. Python 3.10 vs. Python 3.11).
        """
        pass

    @abstractmethod
    def generate_target_deps(self, group: Group) -> str:
        """\
        Loads the dependencies for a particular target.
        E.g. `pip_parse` and `install_deps` for a Python dependency.
        """
        pass

    @abstractmethod
    def generate_build_rules(self, languages: list[Language]) -> str:
        """\
        Loads the build rules necessary to define endpoints and servers.
        This is typically library rules for endpoints (like `py_library`)
        and binary rules for servers (like `py_binary`).
        """
        pass

    @abstractmethod
    def generate_target(self, group: Group) -> str:
        """\
        Generates the target for a particular endpoint group.
        E.g. for Python this is a `py_library` where its deps
        are the set of deps produced by `generate_target_deps`.
        """
        pass

    @abstractmethod
    def generate_server_target(self, language: Language, groups: list[Group]) -> str:
        """\
        Generates the server for a particular language and set of deps.
        This has a set of deps necessary for running the server,
        and then depends on each of the targets generated by `generate_target`.
        """
        pass

    @abstractmethod
    def generate_server(self, language: Language, groups: list[Group]) -> str:
        """\
        Generates the actual server implementation for a language and a set of deps.
        E.g. for Python: an ASGI application that composes all of the endpoints,
        along with an invocation of the ASGI server.
        """
        pass

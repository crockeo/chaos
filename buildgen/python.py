from __future__ import annotations

import textwrap
from pathlib import Path

from packaging.requirements import Requirement

from buildgen.common import BuildGenerator
from buildgen.common import filename_as_target
from buildgen.common import get_toolchain_name
from manifest import Group
from manifest import Language


# TODO: `server` is essentially a reserved keyword in this setup,
# but that's not articulated anywhere in the manifest load / validation


def get_interpreter_name(language: Language) -> str:
    toolchain_name = get_toolchain_name(language)
    return f"{toolchain_name}_interpreter"


def get_server_deps_name(language: Language) -> str:
    toolchain_name = get_toolchain_name(language)
    return f"{toolchain_name}_server_deps"


def get_install_deps_name(language: Language) -> str:
    toolchain_name = get_toolchain_name(language)
    return f"{toolchain_name}_install_deps_server"


def load_requirements_deps(requirement_name: str, dependencies: str) -> str:
    deps_path = Path.cwd() / dependencies

    deps = []
    for line in deps_path.read_text().splitlines():
        line = line.strip()
        if line.startswith("#"):
            continue

        # NOTE: This requires that requirement files
        # have no other text except for comments and requirements.
        req = Requirement(line)
        deps.append(f'{requirement_name}("{req.name}")')
    return ",".join(deps)


class PythonBuildGenerator(BuildGenerator):
    def generate_repository_rules(self) -> str:
        repository_rules = """\
        http_archive(
            name = "rules_python",
            sha256 = "8c8fe44ef0a9afc256d1e75ad5f448bb59b81aba149b8958f02f7b3a98f5d9b4",
            strip_prefix = "rules_python-0.13.0",
            url = "https://github.com/bazelbuild/rules_python/archive/refs/tags/0.13.0.tar.gz",
        )
        load("@rules_python//python:pip.bzl", "pip_parse")
        load("@rules_python//python:repositories.bzl", "python_register_toolchains")
        """
        return textwrap.dedent(repository_rules)

    def generate_toolchain(self, language: Language) -> str:
        toolchain_name = get_toolchain_name(language)
        interpreter_name = get_interpreter_name(language)
        server_deps_name = get_server_deps_name(language)
        install_deps_name = get_install_deps_name(language)
        toolchain = f"""\
        python_register_toolchains(
            name = "{toolchain_name}",
            python_version = "{language.formatted_version()}",
        )

        load("@{toolchain_name}//:defs.bzl", {interpreter_name} = "interpreter")

        pip_parse(
            name = "{server_deps_name}",
            requirements_lock = "//:requirements.txt",
            python_interpreter_target = {interpreter_name},
        )

        load("@{server_deps_name}//:requirements.bzl", {install_deps_name} = "install_deps")

        {install_deps_name}()
        """
        return textwrap.dedent(toolchain)

    def generate_target_deps(self, group: Group) -> str:
        group_deps_name = f"{group.name}_deps"
        requirements_file_target = filename_as_target(group.dependencies)
        interpreter_name = get_interpreter_name(group.language)
        install_deps_name = f"{group.name}_install_deps"

        target_deps = f"""\
        pip_parse(
            name = "{group_deps_name}",
            requirements_lock = "{requirements_file_target}",
            python_interpreter_target = {interpreter_name},
        )

        load("@{group_deps_name}//:requirements.bzl", {install_deps_name} = "install_deps")

        {install_deps_name}()
        """
        return textwrap.dedent(target_deps)

    def generate_build_rules(self) -> str:
        build_rules = """\
        load("@rules_python//python:defs.bzl", "py_binary", "py_library")
        """
        return textwrap.dedent(build_rules)

    def generate_target(self, group: Group) -> str:
        requirement_name = f"requirement_{group.name}"
        rendered_deps = load_requirements_deps(requirement_name, group.dependencies)

        target = f"""\
        load("@{group.name}_deps//:requirements.bzl", {requirement_name} = "requirement")

        py_library(
            name = "{group.name}",
            srcs = ["{filename_as_target(group.filename)}"],
            deps = [{rendered_deps}],
        )
        """
        return textwrap.dedent(target)

    def generate_server_target(self, language: Language, groups: list[Group]) -> str:
        toolchain_name = get_toolchain_name(language)
        server_deps_name = get_server_deps_name(language)
        requirement_name = f"{toolchain_name}_requirement_server"

        group_deps = ",".join(f'":{group.name}"' for group in groups)
        requirements_deps = load_requirements_deps(requirement_name, "requirements.txt")
        server_target = f"""\
        load("@{server_deps_name}//:requirements.bzl", {requirement_name} = "requirement")

        py_binary(
            name = "{toolchain_name}_server",
            srcs = [":{toolchain_name}_server.py"],
            deps = [{group_deps},{requirements_deps}],
        )
        """
        return textwrap.dedent(server_target)

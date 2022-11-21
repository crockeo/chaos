from __future__ import annotations

import textwrap
from collections import defaultdict
from pathlib import Path

from packaging.requirements import Requirement

from buildgen.common import filename_as_target
from buildgen.common import get_toolchain_name
from manifest import Group
from manifest import Language
from manifest import Manifest


RULES_PYTHON = """\
http_archive(
    name = "rules_python",
    sha256 = "8c8fe44ef0a9afc256d1e75ad5f448bb59b81aba149b8958f02f7b3a98f5d9b4",
    strip_prefix = "rules_python-0.13.0",
    url = "https://github.com/bazelbuild/rules_python/archive/refs/tags/0.13.0.tar.gz",
)
load("@rules_python//python:pip.bzl", "pip_parse")
load("@rules_python//python:repositories.bzl", "python_register_toolchains")
"""


LOAD_PY_TARGETS = """\
load("@rules_python//python:defs.bzl", "py_binary", "py_library")
"""


def get_interpreter_name(language: Language) -> str:
    toolchain_name = get_toolchain_name(language)
    return f"{toolchain_name}_interpreter"


def get_server_deps_name(language: Language) -> str:
    toolchain_name = get_toolchain_name(language)
    return f"{toolchain_name}_server_deps"


def get_install_deps_name(language: Language) -> str:
    toolchain_name = get_toolchain_name(language)
    return f"{toolchain_name}_install_deps_server"


def generate_python_toolchain(language: Language) -> str:
    language_id, _ = language.value
    if language_id != "python":
        # TODO: better exception type
        raise ValueError(
            f"Cannot generate Python toolchain for non-Python language: {language_id}"
        )

    toolchain_name = get_toolchain_name(language)
    interpreter_name = get_interpreter_name(language)
    server_deps_name = get_server_deps_name(language)
    install_deps_name = get_install_deps_name(language)
    return textwrap.dedent(
        f"""\
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
    )


def generate_pip_parse(group: Group) -> str:
    target_parts = group.dependencies.split("/")
    if not target_parts:
        # TODO: exception type
        raise Exception("asdfasdfad")

    pip_repo_name = f"{group.name}_deps"
    return textwrap.dedent(
        f"""\
    pip_parse(
        name = "{pip_repo_name}",
        requirements_lock = "{filename_as_target(group.dependencies)}",
        python_interpreter_target = {get_interpreter_name(group.language)},
    )

    load("@{pip_repo_name}//:requirements.bzl", install_deps_{group.name} = "install_deps")
    install_deps_{group.name}()"""
    )


def generate_python_env(group: Group) -> str:
    parts = [
        generate_python_toolchain(group.language),
        generate_pip_parse(group),
    ]
    return "\n".join(parts)


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


def generate_python_group_target(group: Group) -> str:
    requirement_name = f"requirement_{group.name}"

    rendered_deps = load_requirements_deps(requirement_name, group.dependencies)
    return textwrap.dedent(
        f"""\
    load("@{group.name}_deps//:requirements.bzl", {requirement_name} = "requirement")

    py_library(
        name = "{group.name}",
        srcs = ["{filename_as_target(group.filename)}"],
        deps = [{rendered_deps}],
    )
    """
    )


def generate_python_server_targets(manifest: Manifest) -> str:
    # TODO: this is actually super wrong. _always_ generating a python target
    # irrespective of the targets that we're generating seems bad.
    languages_to_groups = defaultdict(list)
    for group in manifest.groups:
        if group.language.id != "python":
            continue
        languages_to_groups[group.language].append(group)

    server_targets = []
    for language, groups in languages_to_groups.items():
        toolchain_name = get_toolchain_name(language)
        server_deps_name = get_server_deps_name(language)
        requirement_name = f"{toolchain_name}_requirement_server"

        group_deps = ",".join(f'":{group.name}"' for group in groups)
        requirements_deps = load_requirements_deps(requirement_name, "requirements.txt")
        server_targets.append(
            textwrap.dedent(
                f"""\
            load("@{server_deps_name}//:requirements.bzl", {requirement_name} = "requirement")

            py_binary(
                name = "{toolchain_name}_server",
                srcs = [":{toolchain_name}_server.py"],
                deps = [{group_deps},{requirements_deps}],
            )
            """
            )
        )

    return "\n".join(server_targets)

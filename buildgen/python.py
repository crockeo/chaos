from __future__ import annotations

import textwrap

from buildgen.common import filename_as_target
from manifest import Group
from manifest import Language


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


def generate_python_toolchain(language: Language) -> str:
    language_id, _ = language.value
    if language_id != "python":
        # TODO: better exception type
        raise ValueError(
            f"Cannot generate Python toolchain for non-Python language: {language_id}"
        )

    return textwrap.dedent(
        f"""\
    python_register_toolchains(
        name = "{language.toolchain_name()}",
        python_version = "{language.formatted_version()}",
    )

    load("@{language.toolchain_name()}//:defs.bzl", "interpreter")

    pip_parse(
        name = "server_deps",
        requirements_lock = "//:requirements.txt",
        python_interpreter_target = interpreter,
    )

    load("@server_deps//:requirements.bzl", install_deps_server = "install_deps")
    install_deps_server()
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
        python_interpreter_target = interpreter,
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

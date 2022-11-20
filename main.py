from collections import defaultdict
from functools import partial
import shutil
import subprocess
import sys
import textwrap
import tempfile
from pathlib import Path
from packaging.requirements import InvalidRequirement
from packaging.requirements import Requirement
from debug import cat_dir

from manifest import Group, Language, Manifest


# TODO
#
# 1. Generate a WORKSPACE / BUILD file in a tmp directory,
#    build a Python library which defines a set of endpoints,
#    load it from an ASGI server,
#    and serve a request.
#
# 2. Do ^ but for multiple endpoints with multiple manifest.yamls.
#    Deal with things like:
#    - Make sure you don't load rules_python multiple times.
#    - Define one toolchain per language being used.
#    - Define one venv per venv.
#    - Load both environments into separate ASGI servers & host.
#
# 3. Try to run multiple venvs under a single ASGI.
#    - Different Python processes with different venvs?
#    - Different venvs for different call paths?
#
#
#
# OTHER RANDOM THOUGHTS:
#
# - This is mostly filling in templates. How about I move it over to jinja2?
#   Then I can get away from most of this manual text munging.

HTTP_ARCHIVE = """\
load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")
"""


RULES_PYTHON = """\
http_archive(
    name = "rules_python",
    sha256 = "8c8fe44ef0a9afc256d1e75ad5f448bb59b81aba149b8958f02f7b3a98f5d9b4",
    strip_prefix = "rules_python-0.13.0",
    url = "https://github.com/bazelbuild/rules_python/archive/refs/tags/0.13.0.tar.gz",
)
load("@rules_python//python:repositories.bzl", "python_register_toolchains")
"""


PY_RULES = """\
load("@rules_python//python:defs.bzl", "py_binary", "py_library")
"""


def filename_as_target(filename: str) -> str:
    directory, _, filename = filename.rpartition("/")
    if not filename:
        return f"//:{directory}"
    return f"//{directory}:{filename}"


def generate_python_toolchain(language: Language) -> str:
    language_id, _ = language.value
    if language_id != "python":
        # TODO: better exception type
        raise ValueError(f"Cannot generate Python toolchain for non-Python language: {language_id}")

    return textwrap.dedent(f"""\
    python_register_toolchains(
        name = "{language.toolchain_name()}",
        python_version = "{language.formatted_version()}",
    )

    load("@{language.toolchain_name()}//:defs.bzl", "interpreter")
    load("@rules_python//python:pip.bzl", "pip_parse")

    pip_parse(
        name = "server_deps",
        requirements_lock = "//:requirements.txt",
        python_interpreter_target = interpreter,
    )
    """)


def generate_pip_parse(group: Group) -> str:
    target_parts = group.dependencies.split("/")
    if not target_parts:
        # TODO: exception type
        raise Exception("asdfasdfad")

    pip_repo_name = f"{group.name}_deps"
    return textwrap.dedent(f"""\
    pip_parse(
        name = "{pip_repo_name}",
        requirements_lock = "{filename_as_target(group.dependencies)}",
        python_interpreter_target = interpreter,
    )

    load("@{pip_repo_name}//:requirements.bzl", install_deps_{group.name} = "install_deps")
    install_deps_{group.name}()""")


def generate_python_env(group: Group) -> str:
    parts = [
        generate_python_toolchain(group.language),
        generate_pip_parse(group),
    ]
    return "\n".join(parts)


def generate_workspace(manifest: Manifest) -> str:
    return "\n".join([
        HTTP_ARCHIVE,
        RULES_PYTHON,
        generate_python_env(manifest.groups[0])
    ])


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
        deps.append(
            f"{requirement_name}(\"{req.name}\")"
        )

    # TODO: this is disgusting little codegen and i hate it
    deps = [
        f"            {dep},"
        for dep in deps
    ]
    rendered_deps = "\n".join(deps)
    return f"\n{rendered_deps}\n        "


def generate_group_target(group: Group) -> str:
    requirement_name = f"requirement_{group.name}"

    rendered_deps = load_requirements_deps(requirement_name, group.dependencies)
    return textwrap.dedent(f"""\
    load("@{group.name}_deps//:requirements.bzl", {requirement_name} = "requirement")

    py_library(
        name = "{group.name}",
        srcs = ["{filename_as_target(group.filename)}"],
        deps = [{rendered_deps}],
    )
    """)


def generate_group_import(group: Group):
    directory, _, filename = group.filename.rpartition("/")
    if not filename:
        filename = directory
        directory = ""

    dot_directory = directory.replace("/", ".")
    underscore_directory = directory.replace("/", "_")
    filename, _, _ = filename.partition(".")
    fully_qualified_name = f"{underscore_directory}_{filename}"

    return textwrap.dedent(f"""\
    from {dot_directory} import {filename} as {fully_qualified_name}
    app.include_router({fully_qualified_name}.router)
    """)


def generate_server_py(manifest: Manifest) -> str:
    server = (Path.cwd() / "server.py").read_text()
    rendered_group_imports = "\n\n".join(
        generate_group_import(group)
        for group in manifest.groups
    )

    return server.replace("# {{REPLACE_ME}}\n", rendered_group_imports)


def generate_server_target(manifest: Manifest) -> str:
    group_deps = ",".join(
        f"\":{group.name}\""
        for group in manifest.groups
    )
    requirements_deps = load_requirements_deps("requirement_server", "requirements.txt")

    return textwrap.dedent(f"""
    load("@server_deps//:requirements.bzl", requirement_server = "requirement")

    py_binary(
        name = "server",
        srcs = [":server.py"],
        deps = [{group_deps},{requirements_deps}],
    )
    """)


def generate_build(manifest: Manifest) -> str:
    return "\n".join([
        PY_RULES,
        *(generate_group_target(group) for group in manifest.groups),
        generate_server_target(manifest),
    ])


def generate_file_exports(file_set: set[str]) -> str:
    exports = [
        f"\"{filename}\""
        for filename in sorted(file_set)
    ]
    exports = ",".join(exports)
    return textwrap.dedent(f"""\
    exports_files([{exports}])
    """)


def print_usage() -> None:
    print("Correct usage:", file=sys.stderr)
    print("  python main.py <path to manifest>", file=sys.stderr)


def main(args: list[str]) -> None:
    manifest_paths = args[1:]
    if not manifest_paths or len(manifest_paths) > 1:
        print_usage()
        raise SystemExit(1)

    manifest_path = manifest_paths[0]
    manifest = Manifest.load(manifest_path)
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        cwd = Path.cwd()
        (tmp_path / "BUILD").write_text(generate_build(manifest))
        (tmp_path / "WORKSPACE").write_text(generate_workspace(manifest))
        (tmp_path / "server.py").write_text(generate_server_py(manifest))
        shutil.copy(cwd / "requirements.txt", tmp_path / "requirements.txt")

        file_sets: dict[Path, set[str]] = defaultdict(set)
        for group in manifest.groups:
            files = [
                group.dependencies,
                group.filename,
            ]

            for filename in files:
                file_path = tmp_path / filename
                file_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(cwd / filename, file_path)
                file_sets[file_path.parent].add(file_path.name)

        for path, file_set in file_sets.items():
            if path == tmp_path:
                # TODO: implement this
                raise NotImplementedError
            (path / "BUILD").write_text(generate_file_exports(file_set))

        targets = []
        for group in manifest.groups:
            targets.append(f"//:{group.name}")

        cat_dir(tmp_path)

        print(tmp_path)
        input()
        subprocess.check_call(
            (
                "bazelisk",
                "run",
                "//:server",
            ),
            cwd=tmp_path,
        )


if __name__ == "__main__":
    main(sys.argv)

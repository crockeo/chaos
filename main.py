from collections import defaultdict
import shutil
import subprocess
import sys
import textwrap
import tempfile
from pathlib import Path
from packaging.requirements import InvalidRequirement
from packaging.requirements import Requirement

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


PY_LIBRARY = """\
load("@rules_python//python:defs.bzl", "py_library")
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


def load_deps(requirement_name: str, group: Group) -> list[str]:
    deps_path = Path.cwd() / group.dependencies

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
    return deps


def generate_group_target(group: Group) -> str:
    requirement_name = f"requirement_{group.name}"

    # TODO: this is disgusting little codegen and i hate it
    deps = load_deps(requirement_name, group)
    deps = [
        f"            {dep},"
        for dep in deps
    ]
    rendered_deps = "\n".join(deps)
    rendered_deps = f"\n{rendered_deps}\n        "

    return textwrap.dedent(f"""\
    load("@{group.name}_deps//:requirements.bzl", {requirement_name} = "requirement")

    py_library(
        name = "{group.name}",
        srcs = ["{filename_as_target(group.filename)}"],
        deps = [{rendered_deps}],
    )
    """)


def generate_build(manifest: Manifest) -> str:
    return "\n".join([
        PY_LIBRARY,
        *(generate_group_target(group) for group in manifest.groups),
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

        (tmp_path / "WORKSPACE").write_text(generate_workspace(manifest))
        (tmp_path / "BUILD").write_text(generate_build(manifest))

        file_sets: dict[Path, set[str]] = defaultdict(set)
        cwd = Path.cwd()
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
                raise NotImplementedError
            (path / "BUILD").write_text(generate_file_exports(file_set))

        targets = []
        for group in manifest.groups:
            targets.append(f"//:{group.name}")

        subprocess.check_call(
            (
                "bazelisk",
                "build",
                *(
                    f"//:{group.name}"
                    for group in manifest.groups
                ),
            ),
            cwd=tmp_path,
        )


if __name__ == "__main__":
    main(sys.argv)

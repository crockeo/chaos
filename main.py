import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
from collections import defaultdict
from pathlib import Path

from buildgen.common import HTTP_ARCHIVE
from buildgen.python import generate_python_env
from buildgen.python import generate_python_group_target
from buildgen.python import generate_python_server_targets
from buildgen.python import LOAD_PY_TARGETS
from buildgen.python import RULES_PYTHON
from debug import cat_dir
from manifest import Group
from manifest import Manifest


# TODO
#
# 1. (DONE)
#    Generate a WORKSPACE / BUILD file in a tmp directory,
#    build a Python library which defines a set of endpoints,
#    load it from an ASGI server,
#    and serve a request.
#
# 2. (TODO)
#    Do ^ but for multiple endpoints with multiple groups.
#    Deal with things like:
#    - Make sure you don't load rules_python multiple times.
#    - Define one toolchain per language being used.
#    - Define one venv per venv.
#    - Load both environments into separate ASGI servers & host.
#
# 3. (TODO)
#    Try to run multiple venvs under a single ASGI.
#    - Different Python processes with different venvs?
#    - Different venvs for different call paths?
#
#
#
# OTHER RANDOM THOUGHTS:
#
# - This is mostly filling in templates. How about I move it over to jinja2?
#   Then I can get away from most of this manual text munging.
#
# - If multiple groups target the same set of requirements,
#   don't create multiple venvs for them! Do only 1 `pip_parse`.
#   Better yet: don't do it on filename quality, do it on equivalence of the sets.
#   It doesn't matter if multiple places refer
#   to different files if they want to install the same stuff.


def generate_workspace(manifest: Manifest) -> str:
    return "\n".join(
        [
            HTTP_ARCHIVE,
            RULES_PYTHON,
            *(generate_python_env(group) for group in manifest.groups),
        ]
    )


def generate_group_import(group: Group):
    directory, _, filename = group.filename.rpartition("/")
    if not filename:
        filename = directory
        directory = ""

    dot_directory = directory.replace("/", ".")
    underscore_directory = directory.replace("/", "_")
    filename, _, _ = filename.partition(".")
    fully_qualified_name = f"{underscore_directory}_{filename}"

    return textwrap.dedent(
        f"""\
    from {dot_directory} import {filename} as {fully_qualified_name}
    app.include_router({fully_qualified_name}.router)
    """
    )


def generate_server_py(manifest: Manifest) -> str:
    server = (Path.cwd() / "server.py").read_text()
    rendered_group_imports = "\n\n".join(
        generate_group_import(group) for group in manifest.groups
    )

    return server.replace("# {{REPLACE_ME}}\n", rendered_group_imports)


def generate_build(manifest: Manifest) -> str:
    return "\n".join(
        [
            LOAD_PY_TARGETS,
            *(generate_python_group_target(group) for group in manifest.groups),
            generate_python_server_targets(manifest),
        ]
    )


def generate_file_exports(file_set: set[str]) -> str:
    exports = [f'"{filename}"' for filename in sorted(file_set)]
    rendered_exports = ",".join(exports)
    return textwrap.dedent(
        f"""\
    exports_files([{rendered_exports}])
    """
    )


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

        # TODO: remove this later...
        if "DEBUG" in os.environ:
            cat_dir(tmp_path)
            print(tmp_path)
            input()

        # TODO: make this run other servers instead of hard-coded toolchain versions...
        subprocess.check_call(
            (
                "bazelisk",
                "run",
                "//:python3_9_server",
            ),
            cwd=tmp_path,
        )


if __name__ == "__main__":
    main(sys.argv)

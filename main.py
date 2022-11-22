import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

import buildgen
from buildgen.common import get_toolchain_name
from debug import cat_dir
from manifest import Group
from manifest import Language
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


def generate_group_import(group: Group):
    directory, _, filename = group.filename.rpartition("/")
    if not filename:
        filename = directory
        directory = ""

    dot_directory = directory.replace("/", ".")
    underscore_directory = directory.replace("/", "_")
    filename, _, _ = filename.partition(".")
    fully_qualified_name = f"{underscore_directory}_{filename}"

    group_import = f"""\
    from {dot_directory} import {filename} as {fully_qualified_name}
    app.include_router({fully_qualified_name}.router)
    """
    return textwrap.dedent(group_import)


def generate_server_py(manifest: Manifest, for_language: Language) -> str:
    server = (Path.cwd() / "server.py").read_text()
    rendered_group_imports = "\n\n".join(
        generate_group_import(group)
        for group in manifest.groups
        if group.language == for_language
    )

    return server.replace("# {{REPLACE_ME}}\n", rendered_group_imports)


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

    cwd = Path.cwd()
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        buildgen.generate_build(tmp_path, manifest)

        # TODO: do server generation in the builder...
        languages = set()
        for group in manifest.groups:
            languages.add(group.language)
        for language in languages:
            server_contents = generate_server_py(manifest, language)
            filename = f"{get_toolchain_name(language)}_server.py"
            (tmp_path / filename).write_text(server_contents)

        # TODO: express this in the manifest somehow...
        shutil.copy(cwd / "requirements.txt", tmp_path / "requirements.txt")
        for path in manifest.iter_files():
            shutil.copy(cwd / path, tmp_dir / path)

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

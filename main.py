import functools
import shutil
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path
from typing import Any
from typing import Callable

import click

import buildgen
from buildgen.common import get_toolchain_name
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


def load_manifest(manifest: str) -> Manifest:
    cwd = Path.cwd()
    return Manifest.load(cwd / manifest)


def do_buildgen(manifest: Manifest, target_path: Path) -> None:
    cwd = Path.cwd()
    buildgen.generate_build(target_path, manifest)

    # TODO: do server generation in the builder...
    languages = set()
    for group in manifest.groups:
        languages.add(group.language)
    for language in languages:
        server_contents = generate_server_py(manifest, language)
        filename = f"{get_toolchain_name(language)}_server.py"
        (target_path / filename).write_text(server_contents)

    # TODO: express this in the manifest somehow...
    shutil.copy(cwd / "requirements.txt", target_path / "requirements.txt")
    for path in manifest.iter_files():
        shutil.copy(cwd / path, target_path / path)


# NOTE: we don't really care about type erasure here,
# because these are only going to be called from
# click's magic internal interface.
def arguments(fn: Callable[..., Any]) -> Callable[..., Any]:
    @click.option(
        "--manifest",
        required=True,
        type=click.Path(exists=True, dir_okay=False, readable=True),
    )
    @functools.wraps(fn)
    def _fn(*args, **kwargs):
        fn(*args, **kwargs)

    return _fn  # type: ignore


@click.group()
def cli():
    pass


@cli.command()
@click.option("--output-dir", type=click.Path(file_okay=False), required=True)
@arguments
def generate(manifest: str, output_dir: str) -> None:
    manifest_obj = load_manifest(manifest)
    output_path = Path(output_dir)
    if not output_path.is_absolute():
        output_path = Path.cwd() / output_path
    output_path.mkdir(parents=True, exist_ok=True)
    do_buildgen(manifest_obj, output_path)


@cli.command()
@click.option("--target", required=True, type=str)
@arguments
def run(manifest: str, target: str) -> None:
    manifest_obj = load_manifest(manifest)
    with tempfile.TemporaryDirectory() as output_dir:
        output_path = Path(output_dir)
        do_buildgen(manifest_obj, output_path)
        subprocess.check_call(
            (
                "bazelisk",
                "run",
                target,
            ),
            cwd=output_path,
        )


if __name__ == "__main__":
    cli()

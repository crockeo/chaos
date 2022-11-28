import functools
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any
from typing import Callable

import click

import buildgen
from manifest import Language
from manifest import Manifest


def load_manifest(manifest: str) -> Manifest:
    cwd = Path.cwd()
    return Manifest.load(cwd / manifest)


def do_buildgen(manifest: Manifest, language: Language, target_path: Path) -> None:
    manifest.groups = [group for group in manifest.groups if group.language == language]

    cwd = Path.cwd()
    buildgen.generate_build(target_path, language, manifest)

    # TODO: express this in the manifest somehow...
    shutil.copy(cwd / "requirements.txt", target_path / "requirements.txt")
    for path in manifest.iter_files():
        shutil.copy(cwd / path, target_path / path)


def get_available_languages() -> list[str]:
    available_languages = []
    for language in Language:
        available_languages.append(language.short_format())
    return available_languages


# NOTE: we don't really care about type erasure here,
# because these are only going to be called from
# click's magic internal interface.
def arguments(fn: Callable[..., Any]) -> Callable[..., Any]:
    @click.option(
        "--manifest",
        required=True,
        type=click.Path(exists=True, dir_okay=False, readable=True),
    )
    @click.option(
        "--language",
        required=True,
        type=click.Choice(get_available_languages()),
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
def generate(manifest: str, language: str, output_dir: str) -> None:
    manifest_obj = load_manifest(manifest)
    output_path = Path(output_dir)
    if not output_path.is_absolute():
        output_path = Path.cwd() / output_path
    output_path.mkdir(parents=True, exist_ok=True)
    do_buildgen(manifest_obj, Language.from_str(language), output_path)


@cli.command()
@arguments
def run(manifest: str, language: str) -> None:
    manifest_obj = load_manifest(manifest)

    cache_dir = Path.home() / ".cache" / "bazel_repositories"
    cache_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as output_dir:
        output_path = Path(output_dir)
        do_buildgen(manifest_obj, Language.from_str(language), output_path)
        subprocess.check_call(
            (
                "bazelisk",
                "run",
                "//:server",
                f"--repository_cache={cache_dir}",
            ),
            cwd=output_path,
        )


if __name__ == "__main__":
    cli()

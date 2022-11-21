import textwrap
from collections import defaultdict
from pathlib import Path

from buildgen.python import generate_python_toolchain
from buildgen.python import PythonBuildGenerator
from manifest import Language
from manifest import Manifest


def generate_toolchain(language: Language) -> str:
    if language.id == "python":
        return generate_python_toolchain(language)
    else:
        # TODO: exception type
        raise Exception(f"Cannot generate toolchain for language `{language.name}`")


def generate_toolchains(manifest: Manifest) -> str:
    languages = {group.language for group in manifest.groups}
    return "\n".join(generate_toolchain(language) for language in languages)


LANGUAGE_TO_GENERATOR = {
    "python": PythonBuildGenerator,
}


def generate_workspace(manifest: Manifest) -> str:
    raise NotImplementedError


def generate_root_build(manifest: Manifest) -> str:
    raise NotImplementedError


def generate_export_builds(manifest: Manifest) -> dict[Path, str]:
    filename_groups: dict[Path, set[str]] = defaultdict(set)
    for group in manifest.groups:
        # TODO: generalize this so people can bring in more deps...
        filenames = {
            group.filename,
            group.dependencies,
        }
        for filename in filenames:
            path = Path(filename)
            filename_groups[path.parent].add(path.name)

    build_files: dict[Path, str] = {}
    for path, filenames in filename_groups.items():
        if path == Path("."):
            # Files are automatically exported to BUILD files in the same directory.
            # So file do not need to be exported from the root directory.
            continue

        rendered_exports = ",".join(f'"{filename}"' for filename in sorted(filenames))
        build_file = f"""\
        exports_files([{rendered_exports}])
        """
        build_file = textwrap.dedent(build_file)
        build_files[path] = build_file

    return build_files


def generate_build(target_dir: Path, manifest: Manifest) -> None:
    (target_dir / "WORKSPACE").write_text(generate_workspace(manifest))
    (target_dir / "BUILD").write_text(generate_root_build(manifest))
    for path, contents in generate_export_builds(manifest).items():
        (target_dir / path).write_text(contents)

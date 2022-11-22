import textwrap
from collections import defaultdict
from pathlib import Path

from buildgen.python import PythonBuildGenerator
from manifest import Group
from manifest import Language
from manifest import Manifest


HTTP_ARCHIVE = """\
load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")
"""

LANGUAGE_TO_GENERATOR = {
    "python": PythonBuildGenerator(),
}


def generate_workspace(manifest: Manifest) -> str:
    language_ids = set()
    languages = set()
    for group in manifest.groups:
        language_ids.add(group.language.id)
        languages.add(group.language)

    sections = []
    if languages:
        sections.append(HTTP_ARCHIVE)

    for language_id in language_ids:
        generator = LANGUAGE_TO_GENERATOR[language_id]
        sections.append(generator.generate_repository_rules())

    for language in sorted(languages, key=lambda language: language.value):
        generator = LANGUAGE_TO_GENERATOR[language.id]
        sections.append(generator.generate_toolchain(language))

    return "\n".join(sections)


def generate_root_build(manifest: Manifest) -> str:
    language_ids = set()
    languages_to_groups: dict[Language, list[Group]] = defaultdict(list)
    for group in manifest.groups:
        language_ids.add(group.language.id)
        languages_to_groups[group.language].append(group)

    sections = []
    for language_id in sorted(language_ids):
        generator = LANGUAGE_TO_GENERATOR[language_id]
        sections.append(generator.generate_build_rules())

    for group in manifest.groups:
        generator = LANGUAGE_TO_GENERATOR[group.language.id]
        sections.append(generator.generate_target(group))

    for language, groups in languages_to_groups.items():
        generator = LANGUAGE_TO_GENERATOR[language.id]
        sections.append(generator.generate_server_target(language, groups))

    return "\n".join(sections)


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
        (target_dir / path).mkdir(parents=True, exist_ok=True)
        (target_dir / path / "BUILD").write_text(contents)

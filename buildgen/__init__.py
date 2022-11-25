import textwrap
from collections import defaultdict
from pathlib import Path

from buildgen.go import GoBuildGenerator
from buildgen.python import PythonBuildGenerator
from manifest import Language
from manifest import Manifest


HTTP_ARCHIVE = """\
load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")
"""

LANGUAGE_TO_GENERATOR = {
    "go": GoBuildGenerator(),
    "python": PythonBuildGenerator(),
}


def generate_workspace(language: Language, manifest: Manifest) -> str:
    generator = LANGUAGE_TO_GENERATOR[language.id]

    sections = [
        HTTP_ARCHIVE,
        generator.generate_toolchain(language),
    ]
    for group in manifest.groups:
        sections.append(generator.generate_target_deps(group))

    return "\n".join(sections)


def generate_root_build(language: Language, manifest: Manifest) -> str:
    generator = LANGUAGE_TO_GENERATOR[language.id]

    sections = [generator.generate_build_rules()]
    for group in manifest.groups:
        sections.append(generator.generate_target(group))
    sections.append(generator.generate_server_target(manifest.groups))

    return "\n".join(sections)


def generate_export_builds(manifest: Manifest) -> dict[Path, str]:
    filename_groups: dict[Path, set[str]] = defaultdict(set)
    for path in manifest.iter_files():
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


def generate_build(target_dir: Path, language: Language, manifest: Manifest) -> None:
    (target_dir / "WORKSPACE").write_text(generate_workspace(language, manifest))
    (target_dir / "BUILD").write_text(generate_root_build(language, manifest))

    for path, contents in generate_export_builds(manifest).items():
        (target_dir / path).mkdir(parents=True, exist_ok=True)
        (target_dir / path / "BUILD").write_text(contents)

    generator = LANGUAGE_TO_GENERATOR[language.id]
    (target_dir / f"server.{language.file_suffix}").write_text(
        generator.generate_server(manifest.groups)
    )

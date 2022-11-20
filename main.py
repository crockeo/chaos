import sys
import textwrap

from manifest import Group, Language, Manifest


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

    load("@{language.toolchain_name()}//:defs.bzl", "interpeter")
    load("@rules_python//:pip.bzl", "pip_parse")
    """)


def generate_pip_parse(group: Group) -> str:
    if not group.dependencies.startswith("/"):
        # TODO: exception type
        raise Exception("must define fully qualified deps file")

    target_parts = group.dependencies.split("/")[1:]
    if not target_parts:
        # TODO: exception type
        raise Exception("asdfasdfad")

    target = "/"
    for part in target_parts[:-1]:
        target = f"{target}/{part}"
    target = f"{target}:{target_parts[-1]}"

    return textwrap.dedent(f"""\
    pip_parse(
        name = "{group.name}_deps",
        requirements_lock = "{target}",
    )
    """)


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


def print_usage() -> None:
    print("Correct usage:", file=sys.stderr)
    print("  python main.py <path to manifest> ...", file=sys.stderr)


def main(args: list[str]) -> None:
    manifest_paths = args[1:]
    if not manifest_paths:
        print_usage()
        raise SystemExit(1)

    for manifest_path in manifest_paths:
        manifest = Manifest.load(manifest_path)
        print(generate_workspace(manifest))


if __name__ == "__main__":
    main(sys.argv)

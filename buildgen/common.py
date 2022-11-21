from manifest import Language


HTTP_ARCHIVE = """\
load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")
"""


def filename_as_target(filename: str) -> str:
    directory, _, filename = filename.rpartition("/")
    if not filename:
        return f"//:{directory}"
    return f"//{directory}:{filename}"


def get_toolchain_name(language: Language) -> str:
    formatted_version = language.formatted_version()
    formatted_version = formatted_version.replace(".", "_")
    return f"{language.id}{formatted_version}"

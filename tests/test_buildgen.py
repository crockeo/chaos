import textwrap
from pathlib import Path
from unittest import mock

import pytest

import buildgen
from buildgen.common import BuildGenerator
from buildgen.common import get_toolchain_name
from manifest import Group
from manifest import Language
from manifest import Manifest


class MockGenerator(BuildGenerator):
    def generate_repository_rules(self) -> str:
        return "mock_repository_rules()\n"

    def generate_toolchain(self, language: Language) -> str:
        return f"mock_toolchain_{get_toolchain_name(language)}()\n"

    def generate_target_deps(self, group: Group) -> str:
        return f"mock_target_deps_{group.name}()\n"

    def generate_build_rules(self) -> str:
        return "mock_build_rules()\n"

    def generate_target(self, group: Group) -> str:
        return f"mock_target_{group.name}()\n"

    def generate_server_target(self, language: Language, groups: list[Group]) -> str:
        rendered_group_names = ",".join(
            group.name for group in sorted(groups, key=lambda group: group.name)
        )
        return f"mock_server_target_{get_toolchain_name(language)}({rendered_group_names})\n"


@pytest.fixture
def use_mock_generator():
    with mock.patch.dict(buildgen.LANGUAGE_TO_GENERATOR, {"python": MockGenerator()}):
        yield


def test_generate_workspace__no_groups():
    workspace = buildgen.generate_workspace(Manifest(groups=[]))
    assert workspace == ""


def test_generate_workspace__one_language(use_mock_generator):
    manifest = Manifest(
        groups=[
            Group(
                name="test",
                language=Language.PYTHON_3_11,
                filename="subdir/something.py",
                endpoints=[],
                dependencies="subdir/requirements.txt",
            ),
        ],
    )
    workspace = buildgen.generate_workspace(manifest)

    expected_workspace = """\
    load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

    mock_repository_rules()

    mock_toolchain_python3_11()

    mock_target_deps_test()
    """
    expected_workspace = textwrap.dedent(expected_workspace)
    assert workspace == expected_workspace


def test_generate_workspace__multiple_same_language(use_mock_generator):
    manifest = Manifest(
        groups=[
            Group(
                name="test",
                language=Language.PYTHON_3_11,
                filename="subdir/something.py",
                endpoints=[],
                dependencies="subdir/requirements.txt",
            ),
            Group(
                name="test2",
                language=Language.PYTHON_3_11,
                filename="subdir/something.py",
                endpoints=[],
                dependencies="subdir/requirements.txt",
            ),
        ],
    )
    workspace = buildgen.generate_workspace(manifest)

    expected_workspace = """\
    load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

    mock_repository_rules()

    mock_toolchain_python3_11()

    mock_target_deps_test()

    mock_target_deps_test2()
    """
    expected_workspace = textwrap.dedent(expected_workspace)
    assert workspace == expected_workspace


def test_generate_workspace__multiple_languages(use_mock_generator):
    manifest = Manifest(
        groups=[
            Group(
                name="test",
                language=Language.PYTHON_3_10,
                filename="subdir/something.py",
                endpoints=[],
                dependencies="subdir/requirements.txt",
            ),
            Group(
                name="test2",
                language=Language.PYTHON_3_11,
                filename="subdir/something.py",
                endpoints=[],
                dependencies="subdir/requirements.txt",
            ),
        ],
    )
    workspace = buildgen.generate_workspace(manifest)

    expected_workspace = """\
    load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

    mock_repository_rules()

    mock_toolchain_python3_10()

    mock_toolchain_python3_11()

    mock_target_deps_test()

    mock_target_deps_test2()
    """
    expected_workspace = textwrap.dedent(expected_workspace)
    assert workspace == expected_workspace


def test_generate_root_build__no_targets():
    root_build = buildgen.generate_root_build(Manifest(groups=[]))
    assert root_build == ""


def test_generate_root_build__one_target(use_mock_generator):
    manifest = Manifest(
        groups=[
            Group(
                name="test",
                language=Language.PYTHON_3_11,
                filename="something.py",
                endpoints=[],
                dependencies="requirements.txt",
            ),
        ],
    )
    root_build = buildgen.generate_root_build(manifest)

    expected_root_build = """\
    mock_build_rules()

    mock_target_test()

    mock_server_target_python3_11(test)
    """
    expected_root_build = textwrap.dedent(expected_root_build)
    assert root_build == expected_root_build


def test_generate_root_build__two_targets_same_language(use_mock_generator):
    manifest = Manifest(
        groups=[
            Group(
                name="test",
                language=Language.PYTHON_3_11,
                filename="something.py",
                endpoints=[],
                dependencies="requirements.txt",
            ),
            Group(
                name="test2",
                language=Language.PYTHON_3_11,
                filename="subdir/something.py",
                endpoints=[],
                dependencies="subdir/requirements.txt",
            ),
        ],
    )
    root_build = buildgen.generate_root_build(manifest)

    expected_root_build = """\
    mock_build_rules()

    mock_target_test()

    mock_target_test2()

    mock_server_target_python3_11(test,test2)
    """
    expected_root_build = textwrap.dedent(expected_root_build)
    assert root_build == expected_root_build


def test_generate_root_build__two_targets_different_language(use_mock_generator):
    manifest = Manifest(
        groups=[
            Group(
                name="test",
                language=Language.PYTHON_3_10,
                filename="something.py",
                endpoints=[],
                dependencies="requirements.txt",
            ),
            Group(
                name="test2",
                language=Language.PYTHON_3_11,
                filename="subdir/something.py",
                endpoints=[],
                dependencies="subdir/requirements.txt",
            ),
        ],
    )
    root_build = buildgen.generate_root_build(manifest)

    expected_root_build = """\
    mock_build_rules()

    mock_target_test()

    mock_target_test2()

    mock_server_target_python3_10(test)

    mock_server_target_python3_11(test2)
    """
    expected_root_build = textwrap.dedent(expected_root_build)
    assert root_build == expected_root_build


def test_generate_export_builds__no_files():
    export_builds = buildgen.generate_export_builds(Manifest(groups=[]))
    assert export_builds == {}


def test_generate_export_builds__root_dir():
    manifest = Manifest(
        groups=[
            Group(
                name="test",
                language=Language.PYTHON_3_11,
                filename="something.py",
                endpoints=[],
                dependencies="requirements.txt",
            ),
        ],
    )
    export_builds = buildgen.generate_export_builds(manifest)
    assert export_builds == {}


def test_generate_export_builds__single_sub_dir():
    manifest = Manifest(
        groups=[
            Group(
                name="test",
                language=Language.PYTHON_3_11,
                filename="subdir/something.py",
                endpoints=[],
                dependencies="subdir/requirements.txt",
            ),
        ],
    )
    export_builds = buildgen.generate_export_builds(manifest)
    assert export_builds == {
        Path("subdir"): 'exports_files(["requirements.txt","something.py"])\n'
    }

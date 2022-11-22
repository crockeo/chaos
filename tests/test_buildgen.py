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

    def generate_build_rules(self) -> str:
        return "mock_build_rules()\n"

    def generate_target(self, group: Group) -> str:
        return f"mock_target_{group.name}\n"


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
    assert workspace == textwrap.dedent(
        """\
        load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

        mock_repository_rules()

        mock_toolchain_python3_11()
        """
    )


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
    assert workspace == textwrap.dedent(
        """\
        load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

        mock_repository_rules()

        mock_toolchain_python3_11()
        """
    )


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
    assert workspace == textwrap.dedent(
        """\
        load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

        mock_repository_rules()

        mock_toolchain_python3_10()

        mock_toolchain_python3_11()
        """
    )


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

from pathlib import Path

import buildgen
from manifest import Group
from manifest import Language
from manifest import Manifest


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
                filename="dir1/something.py",
                endpoints=[],
                dependencies="dir1/requirements.txt",
            ),
        ],
    )
    export_builds = buildgen.generate_export_builds(manifest)
    assert export_builds == {
        Path("dir1"): 'exports_files(["requirements.txt","something.py"])\n'
    }

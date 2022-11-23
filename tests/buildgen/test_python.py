import textwrap

from buildgen import python
from manifest import Group
from manifest import Language


def test_python_build_generator__repository_rules():
    generator = python.PythonBuildGenerator()
    repository_rules = generator.generate_repository_rules()

    expected_repository_rules = """\
    http_archive(
        name = "rules_python",
        sha256 = "8c8fe44ef0a9afc256d1e75ad5f448bb59b81aba149b8958f02f7b3a98f5d9b4",
        strip_prefix = "rules_python-0.13.0",
        url = "https://github.com/bazelbuild/rules_python/archive/refs/tags/0.13.0.tar.gz",
    )
    load("@rules_python//python:pip.bzl", "pip_parse")
    load("@rules_python//python:repositories.bzl", "python_register_toolchains")
    """
    expected_repository_rules = textwrap.dedent(expected_repository_rules)
    assert repository_rules == expected_repository_rules


def test_python_build_generator__toolchain():
    generator = python.PythonBuildGenerator()
    toolchain = generator.generate_toolchain(Language.PYTHON_3_10)

    expected_toolchain = """\
    python_register_toolchains(
        name = "python3_10",
        python_version = "3.10",
    )

    load("@python3_10//:defs.bzl", python3_10_interpreter = "interpreter")

    pip_parse(
        name = "python3_10_server_deps",
        requirements_lock = "//:requirements.txt",
        python_interpreter_target = python3_10_interpreter,
    )

    load("@python3_10_server_deps//:requirements.bzl", python3_10_install_deps_server = "install_deps")

    python3_10_install_deps_server()
    """
    expected_toolchain = textwrap.dedent(expected_toolchain)
    assert toolchain == expected_toolchain


def test_python_build_generator__target_deps():
    generator = python.PythonBuildGenerator()
    target_deps = generator.generate_target_deps(
        Group(
            name="test",
            language=Language.PYTHON_3_10,
            filename="something.py",
            endpoints=[],
            dependencies="requirements.txt",
        ),
    )

    expected_target_deps = """\
    pip_parse(
        name = "test_deps",
        requirements_lock = "//:requirements.txt",
        python_interpreter_target = python3_10_interpreter,
    )

    load("@test_deps//:requirements.bzl", test_install_deps = "install_deps")

    test_install_deps()
    """
    expected_target_deps = textwrap.dedent(expected_target_deps)
    assert target_deps == expected_target_deps


def test_python_build_generator__build_rules():
    generator = python.PythonBuildGenerator()
    build_rules = generator.generate_build_rules()

    expected_build_rules = """\
    load("@rules_python//python:defs.bzl", "py_binary", "py_library")
    """
    expected_build_rules = textwrap.dedent(expected_build_rules)
    assert build_rules == expected_build_rules


def test_python_build_generator__target(tmp_path):
    requirements_txt = """\
    somedep==1.2.3
    """
    requirements_txt = textwrap.dedent(requirements_txt)
    (tmp_path / "requirements.txt").write_text(requirements_txt)

    generator = python.PythonBuildGenerator()
    target = generator.generate_target(
        Group(
            name="test",
            language=Language.PYTHON_3_10,
            filename="something.py",
            endpoints=[],
            dependencies="requirements.txt",
        ),
    )

    expected_target = """\
    load("@test_deps//:requirements.bzl", requirement_test = "requirement")

    py_library(
        name = "test",
        srcs = ["//:something.py"],
        deps = [requirement_test("somedep")],
    )
    """
    expected_target = textwrap.dedent(expected_target)
    assert target == expected_target


def test_python_build_generator__server_target(tmp_path):
    requirements_txt = """\
    somedep==1.2.3
    """
    requirements_txt = textwrap.dedent(requirements_txt)
    (tmp_path / "requirements.txt").write_text(requirements_txt)

    generator = python.PythonBuildGenerator()
    server_target = generator.generate_server_target(
        Language.PYTHON_3_10,
        [
            Group(
                name="test",
                language=Language.PYTHON_3_10,
                filename="something.py",
                endpoints=[],
                dependencies="requirements.txt",
            ),
        ],
    )

    expected_server_target = """\
    load("@python3_10_server_deps//:requirements.bzl", python3_10_requirement_server = "requirement")

    py_binary(
        name = "python3_10_server",
        srcs = [":python3_10_server.py"],
        deps = [":test",python3_10_requirement_server("somedep")],
    )
    """
    expected_server_target = textwrap.dedent(expected_server_target)
    assert server_target == expected_server_target

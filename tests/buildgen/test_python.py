import textwrap

from buildgen import python
from manifest import Group
from manifest import Language


def test_python_build_generator__toolchain():
    generator = python.PythonBuildGenerator()
    toolchain = generator.generate_toolchain(Language.PYTHON_3_10)

    expected_toolchain = """\
    http_archive(
        name = "rules_python",
        sha256 = "8c8fe44ef0a9afc256d1e75ad5f448bb59b81aba149b8958f02f7b3a98f5d9b4",
        strip_prefix = "rules_python-0.13.0",
        url = "https://github.com/bazelbuild/rules_python/archive/refs/tags/0.13.0.tar.gz",
    )
    load("@rules_python//python:pip.bzl", "pip_parse")
    load("@rules_python//python:repositories.bzl", "python_register_toolchains")

    python_register_toolchains(
        name = "python_toolchain",
        python_version = "3.10",
    )

    load("@python_toolchain//:defs.bzl", "interpreter")

    pip_parse(
        name = "server_deps",
        requirements_lock = "//:requirements.txt",
        python_interpreter_target = interpreter,
    )

    load("@server_deps//:requirements.bzl", server_install_deps = "install_deps")

    server_install_deps()
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
        python_interpreter_target = interpreter,
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
        deps = [
            requirement_test("somedep"),
        ],
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
    load("@server_deps//:requirements.bzl", requirement_server = "requirement")

    py_binary(
        name = "server",
        srcs = [":server.py"],
        deps = [
            ":test",
            requirement_server("somedep"),
        ],
    )
    """
    expected_server_target = textwrap.dedent(expected_server_target)
    assert server_target == expected_server_target


def test_python_build_generator__server():
    generator = python.PythonBuildGenerator()
    server = generator.generate_server(
        [
            Group(
                name="test",
                language=Language.PYTHON_3_10,
                filename="path/to/endpoint/something.py",
                endpoints=[],
                dependencies="path/to/endpoint/requirements.txt",
            ),
        ],
    )

    expected_server = """\
    import fastapi
    import uvicorn

    app = fastapi.FastAPI()


    from path.to.endpoint import something as path_to_endpoint_something
    app.include_router(path_to_endpoint_something.router)


    if __name__ == "__main__":
        uvicorn.run("server:app", port=8080, log_level="info")
    """
    expected_server = textwrap.dedent(expected_server)
    assert server == expected_server

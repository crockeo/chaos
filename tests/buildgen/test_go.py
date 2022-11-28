import textwrap

from buildgen import go
from manifest import Endpoint
from manifest import Group
from manifest import Language


def test_go_build_generator__generate_toolchain():
    generator = go.GoBuildGenerator()
    toolchain = generator.generate_toolchain(Language.GO_1_19)

    expected_toolchain = """\
    http_archive(
        name = "io_bazel_rules_go",
        sha256 = "ae013bf35bd23234d1dea46b079f1e05ba74ac0321423830119d3e787ec73483",
        urls = [
            "https://github.com/bazelbuild/rules_go/releases/download/v0.36.0/rules_go-v0.36.0.zip",
        ],
    )

    http_archive(
        name = "bazel_gazelle",
        sha256 = "efbbba6ac1a4fd342d5122cbdfdb82aeb2cf2862e35022c752eaddffada7c3f3",
        urls = [
            "https://mirror.bazel.build/github.com/bazelbuild/bazel-gazelle/releases/download/v0.27.0/bazel-gazelle-v0.27.0.tar.gz",
            "https://github.com/bazelbuild/bazel-gazelle/releases/download/v0.27.0/bazel-gazelle-v0.27.0.tar.gz",
        ],
    )

    load("@io_bazel_rules_go//go:deps.bzl", "go_register_toolchains", "go_rules_dependencies")
    load("@bazel_gazelle//:deps.bzl", "gazelle_dependencies", "go_repository")

    go_rules_dependencies()
    go_register_toolchains(version = "1.19.3")
    gazelle_dependencies()
    """
    expected_toolchain = textwrap.dedent(toolchain)
    assert toolchain == expected_toolchain


def test_go_build_generator__generate_target_deps(tmp_path):
    go_sum = """\
    github.com/mattn/go-runewidth v0.0.7/go.mod h1:H031xJmbD/WCDINGzjvQ9THkh0rPKHF+m2gUSrubnMI=
    github.com/mattn/go-runewidth v0.0.13 h1:lTGmDsbAYt5DmK6OnoV7EuIF1wEIFAcxld6ypU4OSgU=
    github.com/mattn/go-runewidth v0.0.13/go.mod h1:Jdepj2loyihRzMpdS35Xk/zdY8IAYHsh153qUoGf23w=
    golang.org/x/xerrors v0.0.0-20191204190536-9bdfabe68543/go.mod h1:I/5z698sn9Ka8TeJc9MKroUUfqBBauWjQqLJ2OPfmY0=
    golang.org/x/xerrors v0.0.0-20200804184101-5ec99f83aff1/go.mod h1:I/5z698sn9Ka8TeJc9MKroUUfqBBauWjQqLJ2OPfmY0=
    """
    go_sum = textwrap.dedent(go_sum)
    (tmp_path / "go.sum").write_text(go_sum)

    generator = go.GoBuildGenerator()
    target_deps = generator.generate_target_deps(
        Group(
            name="test",
            language=Language.GO_1_19,
            filename="something.go",
            endpoints=[],
            dependencies="go.mod",
        ),
    )

    expected_target_deps = """\
    go_repository(
        name = "github_com_mattn_go_runewidth",
        importpath = "github.com/mattn/go-runewidth",
        sum = "h1:lTGmDsbAYt5DmK6OnoV7EuIF1wEIFAcxld6ypU4OSgU=",
        version = "v0.0.13",
    )
    go_repository(
        name = "golang_org_x_xerrors",
        importpath = "golang.org/x/xerrors",
        sum = "h1:I/5z698sn9Ka8TeJc9MKroUUfqBBauWjQqLJ2OPfmY0=",
        version = "v0.0.0-20200804184101-5ec99f83aff1",
    )
    """
    expected_target_deps = textwrap.dedent(expected_target_deps)
    assert target_deps == expected_target_deps


def test_go_build_generator__generate_build_rules(tmp_path):
    generator = go.GoBuildGenerator()
    build_rules = generator.generate_build_rules()

    expected_build_rules = """\
    load("@io_bazel_rules_go//go:def.bzl", "go_binary", "go_library")
    """
    expected_build_rules = textwrap.dedent(expected_build_rules)
    assert build_rules == expected_build_rules


def test_go_build_generator__generate_target(tmp_path):
    go_mod = """\
    module github.com/crockeo/chaos/fixtures

    go 1.19

    require github.com/Code-Hex/Neo-cowsay/v2 v2.0.4
    """
    go_mod = textwrap.dedent(go_mod)
    (tmp_path / "go.mod").write_text(go_mod)

    generator = go.GoBuildGenerator()
    target = generator.generate_target(
        Group(
            name="test",
            language=Language.GO_1_19,
            filename="something.go",
            endpoints=[],
            dependencies="go.mod",
        ),
    )

    expected_target = """\
    go_library(
        name = "test",
        srcs = ["//:something.go"],
        importpath = "github.com/crockeo/chaos/fixtures",
        deps = [
            "@github_com_Code_Hex_Neo_cowsay_v2//:go_default_library",
        ],
    )
    """
    expected_target = textwrap.dedent(expected_target)
    assert target == expected_target


def test_go_build_generator__generate_server_target():
    generator = go.GoBuildGenerator()
    server_target = generator.generate_server_target(
        [
            Group(
                name="test",
                language=Language.GO_1_19,
                filename="something.go",
                endpoints=[],
                dependencies="go.mod",
            ),
        ],
    )

    expected_server_target = """\
    go_binary(
        name = "server",
        srcs = [":server.go"],
        deps = [
            ":test",
        ],
    )
    """
    expected_server_target = textwrap.dedent(expected_server_target)
    assert server_target == expected_server_target


def test_go_build_generator__generate_server(tmp_path):
    go_mod = """\
    module github.com/crockeo/chaos/fixtures

    go 1.19

    require github.com/Code-Hex/Neo-cowsay/v2 v2.0.4
    """
    go_mod = textwrap.dedent(go_mod)
    (tmp_path / "go.mod").write_text(go_mod)

    generator = go.GoBuildGenerator()
    server = generator.generate_server(
        [
            Group(
                name="test",
                language=Language.GO_1_19,
                filename="something.go",
                endpoints=[Endpoint("HelloWorld")],
                dependencies="go.mod",
            ),
        ],
    )

    expected_server = """\
    package main

    import (
    	"log"
    	"net/http"

    	github_com_crockeo_chaos_fixtures "github.com/crockeo/chaos/fixtures"
    )

    func main() {
    	github_com_crockeo_chaos_fixtures_HelloWorld := github_com_crockeo_chaos_fixtures.NewHelloWorld()
    	http.Handle(github_com_crockeo_chaos_fixtures.HelloWorldPattern, github_com_crockeo_chaos_fixtures_HelloWorld)
    	log.Fatal(http.ListenAndServe("127.0.0.1:8080", nil))
    }
    """  # noqa: E101, W191
    expected_server = textwrap.dedent(expected_server)
    assert server == expected_server

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
    python_version = "{{ python_version }}",
)

load("@python_toolchain//:defs.bzl", "interpreter")

pip_parse(
    name = "server_deps",
    requirements_lock = "//:requirements.txt",
    python_interpreter_target = interpreter,
)

load("@server_deps//:requirements.bzl", server_install_deps = "install_deps")

server_install_deps()

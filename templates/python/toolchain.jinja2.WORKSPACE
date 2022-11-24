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

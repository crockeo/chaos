python_register_toolchains(
    name = "{{ toolchain_name }}",
    python_version = "{{ python_version }}",
)

load("@{{ toolchain_name }}//:defs.bzl", {{ interpreter_name }} = "interpreter")

pip_parse(
    name = "{{ toolchain_name }}_server_deps",
    requirements_lock = "//:requirements.txt",
    python_interpreter_target = {{ interpreter_name }},
)

load("@{{ toolchain_name }}_server_deps//:requirements.bzl", {{ install_deps_name }} = "install_deps")

{{ install_deps_name }}()

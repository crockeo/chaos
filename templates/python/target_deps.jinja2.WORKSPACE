pip_parse(
    name = "{{ group_name }}_deps",
    requirements_lock = "{{ requirements_file_target }}",
    python_interpreter_target = {{ interpreter_name }},
)

load("@{{ group_name }}_deps//:requirements.bzl", {{ group_name }}_install_deps = "install_deps")

{{ group_name }}_install_deps()

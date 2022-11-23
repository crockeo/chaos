load("@{{ toolchain_name }}_server_deps//:requirements.bzl", {{ toolchain_name }}_requirement_server = "requirement")

py_binary(
    name = "{{ toolchain_name }}_server",
    srcs = [":{{ toolchain_name }}_server.py"],
    deps = [
        {% for group in groups %}
        ":{{ group }}",
        {% endfor %}
        {% for requirement in requirements %}
        {{ toolchain_name }}_requirement_server("{{ requirement }}"),
        {% endfor %}
    ],
)

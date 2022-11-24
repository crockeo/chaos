load("@server_deps//:requirements.bzl", requirement_server = "requirement")

py_binary(
    name = "server",
    srcs = [":server.py"],
    deps = [
        {% for group in groups %}
        ":{{ group }}",
        {% endfor %}
        {% for requirement in requirements %}
        requirement_server("{{ requirement }}"),
        {% endfor %}
    ],
)

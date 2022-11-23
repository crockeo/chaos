load("@{{ group_name }}_deps//:requirements.bzl", requirement_{{ group_name }} = "requirement")

py_library(
    name = "{{ group_name }}",
    srcs = ["{{ group_target }}"],
    deps = [
        {% for requirement in requirements %}
        requirement_{{ group_name }}("{{ requirement }}"),
        {% endfor %}
    ],
)

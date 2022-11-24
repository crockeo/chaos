go_library(
    name = "{{ group_name }}",
    srcs = ["{{ group_target }}"],
    deps = [
        {% for requirement in requirements %}
        "{{ requirement }}",
        {% endfor %}
    ],
)

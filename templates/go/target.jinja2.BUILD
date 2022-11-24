go_library(
    name = "{{ group_name }}",
    srcs = ["{{ group_target }}"],
    importpath = "{{ import_path }}",
    deps = [
        {% for requirement in requirements %}
        "{{ requirement }}",
        {% endfor %}
    ],
)

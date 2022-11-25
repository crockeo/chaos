go_library(
    name = "{{ group_name }}",
    srcs = ["{{ group_target }}"],
    importpath = "{{ import_path }}",
    deps = [
        {% for requirement in requirements %}
        "@{{ requirement.target_name }}//:go_default_library",
        {% endfor %}
    ],
)

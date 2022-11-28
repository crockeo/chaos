go_binary(
    name = "server",
    srcs = [":server.go"],
    deps = [
        {% for group in groups %}
        ":{{ group }}",
        {% endfor %}
        {% for requirement in requirements %}
        "{{ requirement }}",
        {% endfor %}
    ],
)

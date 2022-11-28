{% for entry in entries %}
go_repository(
    name = "{{ entry.target_name }}",
    importpath = "{{ entry.path }}",
    sum = "{{ entry.sum }}",
    version = "{{ entry.version }}",
)
{% endfor %}

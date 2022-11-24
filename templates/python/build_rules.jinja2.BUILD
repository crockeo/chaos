load("@rules_python//python:defs.bzl", "py_binary", "py_library")
{% for toolchain_name in toolchain_names %}
load("@{{ toolchain_name }}//:defs.bzl", {{toolchain_name}}_interpreter = "interpreter")
{% endfor %}

from jinja2 import Environment
from jinja2 import FileSystemLoader

from buildgen.common import BuildGenerator
from config import TEMPLATES_DIRECTORY
from manifest import Group
from manifest import Language


class GoBuildGenerator(BuildGenerator):
    def __init__(self):
        self.env = Environment(
            loader=FileSystemLoader(TEMPLATES_DIRECTORY / "python"),
            keep_trailing_newline=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def generate_repository_rules(self) -> str:
        return self.env.get_template("repository_rules.jinja2.WORKSPACE").render()

    def generate_toolchain(self, language: Language) -> str:
        template = self.env.get_template("toolchain.jinja2.WORKSPACE")
        return template.render(
            go_version=language.formatted_version(),
        )

    def generate_target_deps(self, group: Group) -> str:
        raise NotImplementedError

    def generate_build_rules(self) -> str:
        raise NotImplementedError

    def generate_target(self, group: Group) -> str:
        raise NotImplementedError

    def generate_server_target(self, groups: list[Group]) -> str:
        raise NotImplementedError

    def generate_server(self, groups: list[Group]) -> str:
        raise NotImplementedError

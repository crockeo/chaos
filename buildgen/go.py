from jinja2 import Environment
from jinja2 import FileSystemLoader

from buildgen.common import BuildGenerator
from buildgen.common import filename_as_target
from config import TEMPLATES_DIRECTORY
from manifest import Group
from manifest import Language


class GoBuildGenerator(BuildGenerator):
    def __init__(self):
        self.env = Environment(
            loader=FileSystemLoader(TEMPLATES_DIRECTORY / "go"),
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
        # TODO(gobranch): this...is going to be a hard one.
        # how do we generate deps from go.mod w/o gazelle?
        # do we just run gazelle?
        return ""

    def generate_build_rules(self) -> str:
        return self.env.get_template("build_rules.jinja2.BUILD").render()

    def generate_target(self, group: Group) -> str:
        template = self.env.get_template("target.jinja2.BUILD")
        return template.render(
            group_name=group.name,
            group_target=filename_as_target(group.filename),
            # TODO(gobranch): how to do requirements here?
            requirements=[],
        )

    def generate_server_target(self, groups: list[Group]) -> str:
        template = self.env.get_template("server_target.jinja2.BUILD")
        return template.render(
            groups=[group.name for group in groups],
            # TODO(gobranch): how to do requirements here?
            requirements=[],
        )

    def generate_server(self, groups: list[Group]) -> str:
        # TODO(gobranch): how do we want to do this? how is it going to work? :(
        return self.env.get_template("server.jinja2").render()

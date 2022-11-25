from __future__ import annotations

from pathlib import Path

from jinja2 import Environment
from jinja2 import FileSystemLoader
from packaging.requirements import Requirement

from buildgen.common import BuildGenerator
from buildgen.common import filename_as_target
from config import TEMPLATES_DIRECTORY
from manifest import Group
from manifest import Language


# TODO: `server` is essentially a reserved keyword in this setup,
# but that's not articulated anywhere in the manifest load / validation


def load_requirements(requirements_txt: str) -> list[str]:
    requirements_path = Path(requirements_txt)
    if not requirements_path.is_absolute():
        requirements_path = Path.cwd() / requirements_path

    requirements = []
    for line in requirements_path.read_text().splitlines():
        line = line.strip()
        if line.startswith("#"):
            continue

        requirement = Requirement(line)
        requirements.append(requirement.name)
    return requirements


class PythonBuildGenerator(BuildGenerator):
    def __init__(self):
        self.env = Environment(
            loader=FileSystemLoader(TEMPLATES_DIRECTORY / "python"),
            keep_trailing_newline=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def generate_toolchain(self, language: Language) -> str:
        template = self.env.get_template("toolchain.jinja2.WORKSPACE")
        return template.render(
            python_version=language.formatted_version(),
        )

    def generate_target_deps(self, group: Group) -> str:
        template = self.env.get_template("target_deps.jinja2.WORKSPACE")
        return template.render(
            group_name=group.name,
            requirements_file_target=filename_as_target(group.dependencies),
        )

    def generate_build_rules(self) -> str:
        return self.env.get_template("build_rules.jinja2.BUILD").render()

    def generate_target(self, group: Group) -> str:
        template = self.env.get_template("target.jinja2.BUILD")
        return template.render(
            group_name=group.name,
            group_target=filename_as_target(group.filename),
            requirements=load_requirements(group.dependencies),
        )

    def generate_server_target(self, groups: list[Group]) -> str:
        template = self.env.get_template("server_target.jinja2.BUILD")
        return template.render(
            groups=[group.name for group in groups],
            requirements=load_requirements("requirements.txt"),
        )

    def generate_server(self, groups: list[Group]) -> str:
        template = self.env.get_template("server.jinja2")

        targets = []
        for group in groups:
            dirname, _, filename = group.filename.rpartition("/")
            filename, _, _ = filename.rpartition(".")

            dot_directory = dirname.replace("/", ".")
            fully_qualified_name = dirname.replace("/", "_")
            fully_qualified_name = f"{fully_qualified_name}_{filename}"

            targets.append((dot_directory, filename, fully_qualified_name))

        return template.render(
            targets=targets,
        )

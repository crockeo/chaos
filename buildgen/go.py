from buildgen.common import BuildGenerator
from manifest import Group
from manifest import Language


class GoBuildGenerator(BuildGenerator):
    def generate_repository_rules(self) -> str:
        raise NotImplementedError

    def generate_toolchain(self, language: Language) -> str:
        raise NotImplementedError

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

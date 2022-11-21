from buildgen.python import generate_python_toolchain
from manifest import Language
from manifest import Manifest


def generate_toolchain(language: Language) -> str:
    if language.id == "python":
        return generate_python_toolchain(language)
    else:
        # TODO: exception type
        raise Exception(f"Cannot generate toolchain for language `{language.name}`")


def generate_toolchains(manifest: Manifest) -> str:
    languages = {group.language for group in manifest.groups}
    return "\n".join(generate_toolchain(language) for language in languages)

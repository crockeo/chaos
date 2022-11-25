from __future__ import annotations

import json
import re
import subprocess
from collections import defaultdict
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from jinja2 import Environment
from jinja2 import FileSystemLoader

from buildgen.common import BuildGenerator
from buildgen.common import filename_as_target
from config import TEMPLATES_DIRECTORY
from manifest import Group
from manifest import Language


def _target_name(import_path: str) -> str:
    return re.sub(r"[.-_]", "_", import_path)


@dataclass(frozen=True)
class GoRequire:
    path: str
    version: str

    @property
    def target_name(self) -> str:
        return _target_name(self.path)

    @staticmethod
    def from_dict(raw_go_require: dict[str, Any]) -> GoRequire:
        return GoRequire(
            raw_go_require["Path"],
            raw_go_require["Version"],
        )


DATETIME_RE = re.compile(
    r"(?P<year>\d{4})(?P<month>\d{2})(?P<day>\d{2})(?P<hour>\d{2})(?P<minute>\d{2})(?P<second>\d{2})"
)


@dataclass(frozen=True)
class GoSumEntry:
    path: str
    version: str
    sum: str

    @property
    def target_name(self) -> str:
        return _target_name(self.path)

    def parse_version(self) -> tuple[int, ...]:
        # Example input: v0.0.0-20191204190536-9bdfabe68543
        # Example output: (0, 0, 0, 2019, 12, 04, 19, 05, 36)
        version = self.version[len("v") :]
        parts = version.split("-")[:2]

        semver = tuple(int(version) for version in parts[0].split("."))
        if len(parts) == 2:
            datetime_match = DATETIME_RE.match(parts[1])
            if datetime_match is None:
                # TODO: type
                raise Exception("asdfasdf")

            semver = (
                *semver,
                int(datetime_match["year"]),
                int(datetime_match["month"]),
                int(datetime_match["day"]),
                int(datetime_match["hour"]),
                int(datetime_match["minute"]),
                int(datetime_match["second"]),
            )

        return semver


@dataclass(frozen=True)
class GoSum:
    entries: list[GoSumEntry]

    def max_versions(self) -> GoSum:
        path_to_entries: dict[str, list[GoSumEntry]] = defaultdict(list)
        for entry in self.entries:
            path_to_entries[entry.path].append(entry)

        max_entries = []
        for entries in path_to_entries.values():
            max_entries.append(max(entries, key=GoSumEntry.parse_version))
        return GoSum(max_entries)

    @staticmethod
    @lru_cache
    def load(go_sum_path: Path) -> GoSum:
        entries = []
        for line in go_sum_path.read_text().splitlines():
            line = line.strip()
            parts = line.split()
            if len(parts) != 3:
                # TODO: type
                raise Exception()

            path = parts[0]
            version = parts[1]
            sum = parts[2]

            version, _, _ = version.partition("/")

            entries.append(GoSumEntry(path, version, sum))
        return GoSum(entries)


@lru_cache
def _load_go_mod(go_mod_dir: Path) -> dict[str, Any]:
    raw_go_mod = subprocess.check_output(
        (
            "go",
            "mod",
            "edit",
            "-json",
        ),
        cwd=go_mod_dir,
        text=True,
        stderr=subprocess.DEVNULL,
    )
    return json.loads(raw_go_mod)


def _get_import_path(group: Group) -> str:
    go_mod = _load_go_mod(group.dependencies_path.parent)
    return go_mod["Module"]["Path"]


def _get_go_require(group: Group) -> list[GoRequire]:
    go_mod = _load_go_mod(group.dependencies_path.parent)
    return [GoRequire.from_dict(require) for require in go_mod["Require"]]


class GoBuildGenerator(BuildGenerator):
    def __init__(self):
        self.env = Environment(
            loader=FileSystemLoader(TEMPLATES_DIRECTORY / "go"),
            keep_trailing_newline=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def generate_repository_rules(self) -> str:
        return ""

    def generate_toolchain(self, language: Language) -> str:
        template = self.env.get_template("toolchain.jinja2.WORKSPACE")
        return template.render(
            go_version=language.formatted_version(),
        )

    def generate_target_deps(self, group: Group) -> str:
        go_sum = GoSum.load(group.dependencies_path.parent / "go.sum").max_versions()
        template = self.env.get_template("target_deps.jinja2.WORKSPACE")
        return template.render(
            entries=go_sum.entries,
        )

    def generate_build_rules(self) -> str:
        return self.env.get_template("build_rules.jinja2.BUILD").render()

    def generate_target(self, group: Group) -> str:
        go_require = _get_go_require(group)

        template = self.env.get_template("target.jinja2.BUILD")
        return template.render(
            group_name=group.name,
            group_target=filename_as_target(group.filename),
            import_path=_get_import_path(group),
            requirements=go_require,
        )

    def generate_server_target(self, groups: list[Group]) -> str:
        template = self.env.get_template("server_target.jinja2.BUILD")
        return template.render(
            groups=[group.name for group in groups],
            # TODO(gobranch): how to do requirements here?
            requirements=[],
        )

    def generate_server(self, groups: list[Group]) -> str:
        targets = []
        endpoints = []
        for group in groups:
            import_name = _get_import_path(group)
            fully_qualified_name = import_name.replace(".", "_").replace("/", "_")
            targets.append((import_name, fully_qualified_name))
            for endpoint in group.endpoints:
                endpoints.append((fully_qualified_name, endpoint.name))

        template = self.env.get_template("server.jinja2")
        return template.render(
            targets=targets,
            endpoints=endpoints,
        )

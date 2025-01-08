from typing import Iterable, override
from pathlib import Path
from functools import lru_cache

from .file_matcher_api import FileMatcher, FileMatcherFactory


class FileMatcherFactoryBase(FileMatcherFactory):

    def _new_matcher(self, patterns: tuple[str, ...]) -> FileMatcher: ...

    @lru_cache(maxsize=128)
    def _cached_pattern2matcher(self, patterns: tuple[str, ...]) -> FileMatcher:
        return self._new_matcher(patterns)

    @override
    def pattern2matcher(
        self, ignore_patterns: Path | str | Iterable[str] | None = None, ignore_file: Path | str | None = None
    ) -> FileMatcher:
        return self._cached_pattern2matcher(
            _patterns2hashable(ignore_patterns=ignore_patterns, ignore_file=ignore_file)
        )


def _patterns2hashable(
    ignore_patterns: Path | str | Iterable[str] | None = None, ignore_file: Path | str | None = None
) -> tuple[str, ...]:
    match ignore_file:
        case Path():
            ignore_patterns = ignore_file
        case str():
            ignore_patterns = Path(ignore_file)

    match ignore_patterns:
        case tuple() as t:
            return t
        case Path() as path:
            with open(path, 'r') as file:
                return tuple(line.rstrip() for line in file)
        case str():
            return tuple(line.rstrip() for line in ignore_patterns.splitlines())
        case _:
            return tuple(ignore_patterns)

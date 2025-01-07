from typing import Protocol, Iterable
from collections import namedtuple
from pathlib import Path
from functools import lru_cache


FileMatchResult = namedtuple('FileMatchResult', ['matches', 'description', 'by_dir'], defaults=[None, False])

class FileMatcher(Protocol):
    def match(self, path: str, is_dir: bool=False) -> FileMatchResult: ...

class FileMatcherFactory(Protocol):

    def _new_matcher(self, patterns: tuple[str, ...]) -> FileMatcher: ...

    @lru_cache(maxsize=128)
    def _cached_pattern2matcher(self, patterns: tuple[str, ...]) -> FileMatcher:
        return self._new_matcher(patterns)

    def pattern2matcher(
        self, ignore_patterns: Path | str | Iterable[str] | None = None, ignore_file: Path | str | None = None
    ) -> FileMatcher:
        return self._cached_pattern2matcher(self._patterns2hashable(ignore_patterns=ignore_patterns, ignore_file=ignore_file))

    def _patterns2hashable(
        self, ignore_patterns: Path | str | Iterable[str] | None = None, ignore_file: Path | str | None = None
    ) -> tuple[str, ...]:
        match ignore_file:
            case Path():
                ignore_patterns = ignore_file
            case str():
                ignore_patterns = Path(ignore_file)

        match ignore_patterns:
            case tuple():
                return ignore_patterns
            case Path() as path:
                with open(path, 'r') as file:
                    return tuple(line.rstrip() for line in file)
            case str():
                return tuple(line.rstrip() for line in ignore_patterns.splitlines())
            case _:
                return tuple(ignore_patterns)



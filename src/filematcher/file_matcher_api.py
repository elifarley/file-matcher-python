from typing import Protocol
from collections import namedtuple


FileMatchResult = namedtuple('FileMatchResult', ['matches', 'description', 'by_dir'], defaults=[None, False])

class FileMatcher(Protocol):
    def match(self, path: str, is_dir: bool=False) -> FileMatchResult: ...

class FileMatcherFactory(Protocol):
    def pattern2matcher(self, patterns: list[str] | tuple[str, ...]) -> FileMatcher: ...


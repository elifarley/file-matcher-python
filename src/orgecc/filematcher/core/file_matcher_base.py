from typing import override
from functools import lru_cache

from ..file_matcher_api import FileMatcher, FileMatcherFactory, DenyPatternSource


class FileMatcherFactoryBase(FileMatcherFactory):

    def _new_matcher(self, patterns: tuple[str, ...]) -> FileMatcher: ...

    @lru_cache(maxsize=128)
    def _cached_pattern2matcher(self, patterns: tuple[str, ...]) -> FileMatcher:
        return self._new_matcher(patterns)

    @override
    def pattern2matcher(
        self,
        deny_source: DenyPatternSource
    ) -> FileMatcher:
        return self._cached_pattern2matcher(deny_source.deny_patterns)

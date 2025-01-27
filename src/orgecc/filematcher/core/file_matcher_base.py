from typing import override
from functools import lru_cache

from ..file_matcher_api import FileMatcher, FileMatcherFactory, DenyPatternSource, AllowPatternSource


class FileMatcherFactoryBase(FileMatcherFactory):

    def _new_matcher(
        self, deny_patterns: tuple[str, ...],
        allow_patterns: tuple[str, ...] = tuple()
    ) -> FileMatcher: ...

    @lru_cache(maxsize=128)
    def _cached_pattern2matcher(
        self, deny_patterns: tuple[str, ...],
        allow_patterns: tuple[str, ...] = tuple()
    ) -> FileMatcher:
        return self._new_matcher(deny_patterns, allow_patterns)

    @override
    def pattern2matcher(
        self,
        deny_source: DenyPatternSource,
        allow_source: AllowPatternSource | None = None
    ) -> FileMatcher:
        return self._cached_pattern2matcher(
            deny_source.deny_patterns,
            allow_source.allow_patterns if allow_source is not None else tuple()
        )

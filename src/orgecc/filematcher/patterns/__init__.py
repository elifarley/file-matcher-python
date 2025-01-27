from importlib.resources.abc import Traversable
from pathlib import PurePath
from typing import Iterable

from .pattern_kit import DenyPatternSourceImpl, DenyPatternSourceGroup
from ..file_matcher_api import DenyPatternSource

__all__ = ('new_deny_pattern_source', 'merge_deny_pattern_sources')

def new_deny_pattern_source(
    patterns: str | Iterable[str] | None = None,
    file: str | PurePath | Traversable | None = None,
) -> DenyPatternSource | None:
    if not patterns and not file:
        return None
    return DenyPatternSourceImpl(patterns=patterns, file=file)

def merge_deny_pattern_sources(base: DenyPatternSource, main: DenyPatternSource) -> DenyPatternSource:
    return DenyPatternSourceGroup(deny_base=base, deny_main = main)

from typing import Iterable
from pathlib import Path
from ..file_matcher_api import DenyPatternSource
from .pattern_kit import DenyPatternSourceImpl, DenyPatternSourceGroup

__all__ = ('new_deny_pattern_source', 'merge_deny_pattern_sources')

def new_deny_pattern_source(
    patterns: str | Iterable[str] | None = None,
    file: str | Path | None = None,
) -> DenyPatternSource:
    return DenyPatternSourceImpl(patterns=patterns, file=file)

def merge_deny_pattern_sources(base: DenyPatternSource, main: DenyPatternSource) -> DenyPatternSource:
    return DenyPatternSourceGroup(deny_base=base, deny_main = main)

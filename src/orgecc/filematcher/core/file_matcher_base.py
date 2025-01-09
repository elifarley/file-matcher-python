from typing import Iterable, override
from pathlib import Path
from functools import lru_cache

from ..file_matcher_api import FileMatcher, FileMatcherFactory


class FileMatcherFactoryBase(FileMatcherFactory):

    def _new_matcher(self, patterns: tuple[str, ...]) -> FileMatcher: ...

    @lru_cache(maxsize=128)
    def _cached_pattern2matcher(self, patterns: tuple[str, ...]) -> FileMatcher:
        return self._new_matcher(patterns)

    @override
    def pattern2matcher(
        self,
        ignore_patterns: Path | str | Iterable[str] | None = None,
        ignore_file: Path | str | None = None,
        base_ignore_patterns: Path | str | Iterable[str] | None = None,
        base_ignore_file: Path | str | None = None
    ) -> FileMatcher:
        return self._cached_pattern2matcher(
            _patterns2hashable(
                ignore_patterns=ignore_patterns,
                ignore_file=ignore_file,
                base_ignore_patterns=base_ignore_patterns,
                base_ignore_file=base_ignore_file
            )
        )


def _patterns2hashable(
    ignore_patterns: Path | str | Iterable[str] | None = None,
    ignore_file: Path | str | None = None,
    base_ignore_patterns: Path | str | Iterable[str] | None = None,
    base_ignore_file: Path | str | None = None
) -> tuple[str, ...]:
    """Convert various pattern inputs into a hashable tuple of patterns without duplicates.

    Processes both base and regular ignore patterns, with base patterns taking precedence
    (appearing first in the resulting tuple). Empty lines and comments are filtered out.

    Args:
        ignore_patterns: Regular patterns to ignore
        ignore_file: Path to file containing regular patterns
        base_ignore_patterns: Base patterns to ignore (applied first)
        base_ignore_file: Path to file containing base patterns

    Returns:
        Tuple of patterns with base patterns first, followed by regular patterns.

    Examples:
        >>> _patterns2hashable(ignore_patterns="*.pyc")
        ('*.pyc',)
        >>> _patterns2hashable(base_ignore_patterns=["*.tmp"], ignore_patterns=["*.pyc", "*.tmp"])
        ('*.tmp', '*.pyc')
    """

    def _simple_patterns2hashable(
        ignore_patterns: Path | str | Iterable[str] | None = None, ignore_file: Path | str | None = None
    ):
        match ignore_file:
            case Path():
                ignore_patterns = ignore_file
            case str():
                ignore_patterns = Path(ignore_file)

        match ignore_patterns:
            case tuple() as t:
                return tuple(line for line in t if line.strip() and not line.startswith('#'))
            case Path() as path:
                with open(path, 'r') as file:
                    return tuple(line.rstrip() for line in file if line.strip() and not line.startswith('#'))
            case str():
                return tuple(line.rstrip() for line in ignore_patterns.splitlines() if line.strip() and not line.startswith('#'))
            case _:
                return tuple(line for line in ignore_patterns if line.strip() and not line.startswith('#'))


    # Combine patterns, removing duplicates while preserving order
    # Base patterns come first, followed by regular patterns
    seen = set()
    final_patterns = []

    base_patterns = _simple_patterns2hashable(base_ignore_patterns, base_ignore_file)
    regular_patterns = _simple_patterns2hashable(ignore_patterns, ignore_file)
    for pattern in base_patterns + regular_patterns:
        if pattern not in seen:
            seen.add(pattern)
            final_patterns.append(pattern)

    return tuple(final_patterns)

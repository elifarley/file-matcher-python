from pathlib import Path
from typing import Iterable, override
from dataclasses import dataclass

from ..file_matcher_api import DenyPatternSource, AllowPatternSource


class PatternSourceBase():
    """
    Holds either a list of patterns or a path to a file containing patterns.
    You cannot provide both at once.
    Args:
        patterns: Individual patterns to ignore, can be a single pattern
                       or an iterable of patterns
        file: Path to a file containing patterns (e.g., .gitignore)
    """
    def __init__(
        self,
        patterns: str | Iterable[str] | None = None,
        file: str | Path | None = None,
    ):
        if patterns and file:
            raise ValueError("Cannot provide both patterns and file for PatternSource.")
        self.patterns = patterns
        self.file = Path(file) if file else None

    def __repr__(self):
        classname = self.__class__.__name__
        if self.file:
            return f'{classname}(file={self.file})'
        if self.patterns is not None:
            return f'{classname}(patterns={self.patterns})'
        return f'{classname}()'

    def canon_src(self):
        match self.file:
            case Path() as path:
                return path
            case str() as strpath:
                return Path(strpath)
            case _:
                return self.patterns


class DenyPatternSourceImpl(PatternSourceBase, DenyPatternSource):
    """
    Holds either a list of patterns or a path to a file containing patterns.
    You cannot provide both at once.
    Args:
        patterns: Individual patterns to deny, can be a single pattern
                       or an iterable of patterns
        file: Path to a file containing deny patterns (e.g., .gitignore)
    """
    def __init__(
        self,
        patterns: str | Iterable[str] | None = None,
        file: str | Path | None = None,
    ):
        super().__init__(patterns=patterns, file=file)

    @override
    @property
    def deny_patterns(self) -> tuple[str, ...]:
        match self.canon_src():
            case Path() as path:
                with open(path, 'r') as file:
                    return tuple(line.rstrip() for line in file if line.strip() and not line.startswith('#'))
            case str() as patterns:
                return tuple(line.rstrip() for line in patterns.splitlines() if line.strip() and not line.startswith('#'))
            case _ as other:
                return tuple(line for line in other if line.strip() and not line.startswith('#'))


class AllowPatternSourceImpl(PatternSourceBase, AllowPatternSource):
    """
    Holds either a list of patterns or a path to a file containing patterns.
    You cannot provide both at once.
    Args:
        patterns: Individual patterns to allow, can be a single pattern
                       or an iterable of patterns
        file: Path to a file containing allow patterns (e.g., .gitignore)
    """
    def __init__(
        self,
        patterns: str | Iterable[str] | None = None,
        file: str | Path | None = None,
    ):
        super().__init__(patterns=patterns, file=file)

    @override
    @property
    def allow_patterns(self) -> set[str]:
        match self.canon_src():
            case Path() as path:
                with open(path, 'r') as file:
                    return set(line.rstrip() for line in file if line.strip() and not line.startswith('#'))
            case str() as patterns:
                return set(line.rstrip() for line in patterns.splitlines() if line.strip() and not line.startswith('#'))
            case _ as other:
                return set(line for line in t if line.strip() and not line.startswith('#'))


@dataclass
class DenyPatternSourceGroup(DenyPatternSource):
    deny_base: DenyPatternSource
    deny_main: DenyPatternSource

    @override
    @property
    def deny_patterns(self) -> tuple[str, ...]:
        """Convert various pattern inputs into a hashable tuple of patterns without duplicates.

        Processes both base and regular ignore patterns, with base patterns taking precedence
        (appearing first in the resulting tuple). Empty lines and comments are filtered out.

        Args:
            ignore_patterns: Main patterns to ignore, can be a single pattern
                           or an iterable of patterns
            base_ignore_patterns: Base patterns to ignore (applied first).

        Returns:
            Tuple of patterns with base patterns first, followed by regular patterns.

        Examples:
            ignore=PatternSource(patterns=["*.pyc", "build/"])

            >>> _patterns2hashable(ignore_patterns=DenyPatternSourceImpl(patterns="*.pyc")
            ('*.pyc',)
            >>> _patterns2hashable(base_ignore_patterns=DenyPatternSourceImpl(patterns=["*.tmp"]), ignore_patterns=DenyPatternSourceImpl(patterns=["*.pyc", "*.tmp"]))
            ('*.tmp', '*.pyc')
        """

        # Combine patterns, removing duplicates while preserving order
        # Base patterns come first, followed by regular patterns
        seen = set()
        final_patterns = []

        for pattern in self.deny_base.deny_patterns + self.deny_main.deny_patterns:
            if pattern not in seen:
                seen.add(pattern)
                final_patterns.append(pattern)

        return tuple(final_patterns)

class DenyAllowPatterns(DenyPatternSource, AllowPatternSource):
    deny: DenyPatternSource
    allow: AllowPatternSource

    @override
    def deny_patterns(self) -> tuple[str, ...]:
        return self.deny.deny_patterns

    @override
    def allow_patterns(self) -> set[str]:
        return self.allow.allow_patterns

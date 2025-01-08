from typing import Protocol, Iterable
from collections import namedtuple
from pathlib import Path


FileMatchResult = namedtuple('FileMatchResult', ['matches', 'description', 'by_dir'], defaults=[None, False])
"""
Represents the result of a file matching operation.

Attributes:
    matches (bool): Whether the path matches the pattern
    description (str | None): Description of the match result, useful for debugging
    by_dir (bool): Whether the match was determined by directory status, defaults to False
"""

class FileMatcher(Protocol):
    """
    Protocol defining the interface for file pattern matching implementations.

    This protocol allows for different implementations of file matching logic
    while maintaining a consistent interface.
    """

    def match(self, path: str, is_dir: bool=False) -> FileMatchResult:
        """
        Check if a given path matches the configured patterns.

        Args:
            path: The path to check against the patterns
            is_dir: Whether the path represents a directory

        Returns:
            FileMatchResult containing the match result and description
        """
        ...

class FileMatcherFactory(Protocol):
    """
    Protocol defining the interface for creating file matcher instances.

    This factory protocol allows for different implementations of pattern matching
    while maintaining a consistent way to create matcher instances.
    """

    def pattern2matcher(
        self, ignore_patterns: Path | str | Iterable[str] | None = None, ignore_file: Path | str | None = None
    ) -> FileMatcher:
        """
        Create a new matcher instance from patterns or pattern files.

        Args:
            ignore_patterns: Individual patterns to ignore, can be a single pattern
                           or an iterable of patterns
            ignore_file: Path to a file containing patterns (e.g., .gitignore)

        Returns:
            A FileMatcher instance configured with the specified patterns
        """
        ...

    def __enter__(self): ...
    def __exit__(self, exc_type, exc_val, exc_tb): ...

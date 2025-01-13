import tempfile
from typing import override
from pathspec import GitIgnoreSpec

from .file_matcher_base import FileMatcherFactoryBase
from ..file_matcher_api import FileMatcher, FileMatchResult

class ExtLibPathspecMatcherFactory(FileMatcherFactoryBase):
    """
    This factory creates matchers that delegate pattern matching to the
    external library 'pathspec'.
    """
    def __enter__(self):
        """Context manager entry point."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit point."""
        pass

    @override
    def _new_matcher(self, patterns: tuple[str, ...]) -> FileMatcher:
        """
        Create a new matcher instance for the given patterns.

        Args:
            patterns: A tuple of gitignore pattern strings.

        Returns:
            A FileMatcher instance configured with the given patterns.
        """
        return _ExtLibPathspecMatcher(patterns)


class _ExtLibPathspecMatcher(FileMatcher):
    """
    Implementation of gitignore pattern matching using the external library 'pathspec'.
    """

    __slots__ = ('ext_matcher')

    def __init__(self, patterns: tuple[str, ...], base_path: str = "."):
        """
        Initialize `self.ext_matcher` with a list of patterns.

        Args:
            patterns: list of gitignore pattern strings.
            base_path: Base directory for relative patterns.
        """
        self.ext_matcher = GitIgnoreSpec.from_lines(patterns)


    @override
    def match(self, path: str, is_dir: bool=False) -> FileMatchResult:
        """
        Calls the external library to get the result.

        Args:
            path: The path to check
            is_dir: Whether the path represents a directory

        Returns:
            FileMatchResult containing the match result and description
        """

        path_is_dir = True if is_dir else path.endswith('/')
        ext_match =  self.ext_matcher.check_file(path)
        return FileMatchResult(ext_match.include == False, f'ext-lib: pathspec (index: {ext_match.index})')


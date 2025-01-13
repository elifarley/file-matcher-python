import tempfile
from typing import override
import gitignorefile

from .file_matcher_base import FileMatcherFactoryBase
from ..file_matcher_api import FileMatcher, FileMatchResult

class ExtLibGitignorefileMatcherFactory(FileMatcherFactoryBase):
    """
    This factory creates matchers that delegate pattern matching to the
    external library 'gitignorefile'.
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
        return _ExtLibGitignorefileMatcher(patterns)


class _ExtLibGitignorefileMatcher(FileMatcher):
    """
    Implementation of gitignore pattern matching using the external library 'gitignorefile'.
    """

    __slots__ = ('ext_matcher')

    _true = FileMatchResult(True, f'ext-lib: gitignorefile')
    _false = FileMatchResult(False, f'ext-lib: gitignorefile')

    def __init__(self, patterns: tuple[str, ...], base_path: str = "."):
        """
        Initialize `self.ext_matcher` with a list of patterns.

        Args:
            patterns: list of gitignore pattern strings.
            base_path: Base directory for relative patterns.
        """
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.gitignore') as temp_file:
            # Write each pattern on a new line
            for pattern in patterns:
                temp_file.write(f"{pattern}\n")
            temp_file.close()
            try:
                self.ext_matcher = gitignorefile.parse(temp_file.name)
            finally:
                import os
                os.remove(temp_file.name)


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
        ext_match =  self.ext_matcher(path, path_is_dir)
        return _ExtLibGitignorefileMatcher._true if ext_match else _ExtLibGitignorefileMatcher._false

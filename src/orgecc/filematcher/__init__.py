from functools import cached_property
from enum import Enum, auto

from .file_matcher_api import FileMatcherFactory, FileMatcher, DenyPatternSource

__all__ = ('get_factory', 'MatcherImplementation', 'FileMatcherFactory', 'FileMatcher', 'DenyPatternSource')

class MatcherImplementation(Enum):
    """Defines available matcher implementation types."""
    PURE_PYTHON = auto()
    GIT = auto()
    EXTLIB_GITIGNOREFILE = auto()
    EXTLIB_PATHSPEC = auto()

class MatcherFactoryRegistry:
    """Registry maintaining different matcher factory implementations."""

    @cached_property
    def pure_python_factory(self) -> FileMatcherFactory:
        from .core.file_matcher_python import PurePythonMatcherFactory
        return PurePythonMatcherFactory()

    @cached_property
    def git_native_factory(self) -> FileMatcherFactory:
        from .core.file_matcher_git  import GitNativeMatcherFactory
        return GitNativeMatcherFactory()

    @cached_property
    def extlib_gitignorefile_factory(self) -> FileMatcherFactory:
        from .core.file_matcher_ext_gitignorefile import ExtLibGitignorefileMatcherFactory
        return ExtLibGitignorefileMatcherFactory()

    @cached_property
    def extlib_pathspec_factory(self) -> FileMatcherFactory:
        from .core.file_matcher_ext_pathspec import ExtLibPathspecMatcherFactory
        return ExtLibPathspecMatcherFactory()

    def get_factory(self, matcher_implementation: MatcherImplementation = MatcherImplementation.PURE_PYTHON) -> FileMatcherFactory:
        if matcher_implementation == MatcherImplementation.PURE_PYTHON:
            return self.pure_python_factory

        if matcher_implementation == MatcherImplementation.GIT:
            return self.git_native_factory

        if matcher_implementation == MatcherImplementation.EXTLIB_GITIGNOREFILE:
            return self.extlib_gitignorefile_factory

        if matcher_implementation == MatcherImplementation.EXTLIB_PATHSPEC:
            return self.extlib_pathspec_factory

        raise NotImplementedError(str(matcher_implementation))

_registry = MatcherFactoryRegistry()
def get_factory(matcher_implementation: MatcherImplementation = MatcherImplementation.PURE_PYTHON) -> FileMatcherFactory:
    return _registry.get_factory(matcher_implementation)

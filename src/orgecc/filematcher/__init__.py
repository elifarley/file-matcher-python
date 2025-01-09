from functools import cached_property
from enum import Enum, auto

from .file_matcher_api import FileMatcherFactory, FileMatcher
from .core  import GitNativeMatcherFactory
from .core import PurePythonMatcherFactory

__all__ = ('get_factory', 'MatcherImplementation', 'FileMatcherFactory', 'FileMatcher')

class MatcherImplementation(Enum):
    """Defines available matcher implementation types."""
    PURE_PYTHON = auto()
    GIT = auto()
    EXTERNAL_LIB = auto()

class MatcherFactoryRegistry:
    """Registry maintaining different matcher factory implementations."""

    @cached_property
    def git_native_factory(self) -> FileMatcherFactory:
        return GitNativeMatcherFactory()

    @cached_property
    def pure_python_factory(self) -> FileMatcherFactory:
        return PurePythonMatcherFactory()

    def get_factory(self, matcher_implementation: MatcherImplementation = MatcherImplementation.PURE_PYTHON) -> FileMatcherFactory:
        if matcher_implementation == MatcherImplementation.PURE_PYTHON:
            return self.pure_python_factory

        if matcher_implementation == MatcherImplementation.GIT:
            return self.git_native_factory

        raise NotImplementedError(str(matcher_implementation))

_registry = MatcherFactoryRegistry()
def get_factory(matcher_implementation: MatcherImplementation = MatcherImplementation.PURE_PYTHON) -> FileMatcherFactory:
    return _registry.get_factory(matcher_implementation)

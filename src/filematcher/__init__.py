from version import __version__
from functools import cached_property

from .file_matcher_api import FileMatcherFactory, FileMatcher
from .file_matcher_git import GitNativeMatcherFactory
from .file_matcher_python import PurePythonMatcherFactory

__all__ = ('get_factory_context', 'FileMatcherFactory', 'FileMatcher')

class FactoryProvider:
    @cached_property
    def git_native_factory(self) -> FileMatcherFactory:
        return GitNativeMatcherFactory()

    @cached_property
    def pure_python_factory(self) -> FileMatcherFactory:
        return PurePythonMatcherFactory()

    def get_factory(self, pure_python: bool = True) -> FileMatcherFactory:
        return self.pure_python_factory if pure_python else self.git_native_factory

_provider = FactoryProvider()
def get_factory_context(pure_python: bool = True):
    return _provider.get_factory(pure_python)

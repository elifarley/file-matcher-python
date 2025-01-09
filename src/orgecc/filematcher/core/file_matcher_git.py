import subprocess
import os
import tempfile
from typing import Protocol, NamedTuple, Iterable, override
from collections import namedtuple
from threading import Lock
from .file_matcher_base import FileMatcherFactoryBase
from orgecc.filematcher.file_matcher_api import FileMatcher, FileMatchResult

class _GitContext(Protocol):
    def initialize_matcher(self, instance_id: int, patterns: tuple[str, ...]) -> None: ...
    def cleanup_matcher(self, instance_id: int) -> None: ...
    def run_git_check(self, instance_id: int, path: str) -> FileMatchResult: ...

class _GitIgnoreNativeMatcher(FileMatcher):
    def __init__(
        self,
        patterns: tuple[str, ...],
        instance_id: int,
        git_context: _GitContext
    ):
        self._patterns = patterns
        self._instance_id = instance_id
        self._git_context = git_context
        self._initialized = False

    def _initialize(self):
        if self._initialized:
            return
        self._git_context.initialize_matcher(self._instance_id, self._patterns)
        self._initialized = True

    def __del__(self):
        self._git_context.cleanup_matcher(self._instance_id)

    @override
    def match(self, path: str, is_dir: bool=False) -> FileMatchResult:
        self._initialize()
        return self._git_context.run_git_check(self._instance_id, path)

class GitNativeMatcherFactory(_GitContext, FileMatcherFactoryBase):
    def __init__(self):
        self._lock = Lock()
        self._temp_dir = None
        self._config_dir = None
        self._env = None
        self._git_initialized = False
        self._instance_counter = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._temp_dir:
            try:
                subprocess.run(['rm', '-rf', self._config_dir], check=False)
                subprocess.run(['rm', '-rf', self._temp_dir], check=False)
            except:
                pass

    @override
    def _new_matcher(self, patterns: tuple[str, ...]) -> FileMatcher:
        with self._lock:
            self._instance_counter += 1
            instance_id = self._instance_counter
        return _GitIgnoreNativeMatcher(patterns, instance_id, self)

    def cleanup_matcher(self, instance_id: int) -> None:
        if self._temp_dir:
            try:
                os.remove(self._instance_exclude_file(instance_id))
            except (OSError, FileNotFoundError):
                pass

    def _instance_exclude_file(self, instance_id: int) -> str:
        return os.path.join(self._temp_dir, '.git', 'info', f'exclude-{instance_id}')

    def _ensure_initialized(self):
        if not self._temp_dir:
            self._config_dir = tempfile.mkdtemp()
            self._temp_dir = tempfile.mkdtemp()
            self._env = os.environ.copy()
            self._env['GIT_CONFIG_GLOBAL'] = os.path.join(self._config_dir, 'gitconfig')
            self._env['XDG_CONFIG_HOME'] = self._config_dir

        if not self._git_initialized:
            subprocess.run(
                ['git', 'init'],
                cwd=self._temp_dir,
                env=self._env,
                capture_output=True
            )
            self._git_initialized = True

    def initialize_matcher(self, instance_id: int, patterns: tuple[str, ...]):
        self._ensure_initialized()
        with open(self._instance_exclude_file(instance_id), 'w') as f:
            f.write('\n'.join(patterns))

    def run_git_check(self, instance_id: int, path: str) -> FileMatchResult:
        try:
            process = subprocess.run(
                ['git', '-c', f'core.excludesFile={self._instance_exclude_file(instance_id)}',
                 'check-ignore', '-v', path],
                cwd=self._temp_dir,
                env=self._env,
                capture_output=True,
                text=True,
                check=False  # Add explicit check=False
            )
        except subprocess.SubprocessError as e:
            return FileMatchResult(False, f"Error: {str(e)}")

        matches = process.returncode == 0
        description = None
        if matches:
            try:
                parts = process.stdout.strip().split(':')[-2:]
                if len(parts) >= 2:
                    *_, line_num, pattern = parts
                    pattern = pattern.split('\t')[0].strip()
                    if len(pattern):
                        matches = pattern[0] != '!'
                    description = f"'{pattern}' @ {line_num.strip()}"
                else:
                    description = "Ignored (output format unexpected)"
            except ValueError as e:
                description = f"Ignored ({e})"

        return FileMatchResult(matches, description)

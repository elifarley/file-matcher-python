from pathlib import Path
from typing import Generator, Iterable
import logging
from dataclasses import dataclass

from orgecc.filematcher import get_factory, MatcherImplementation, FileMatcher


logger = logging.getLogger(__name__)

@dataclass
class WalkStats:
    """Statistics collected during directory traversal."""
    ignored_count: int = 0
    yielded_count: int = 0

class DirectoryWalker:
    """
    Walks directory trees respecting potentially multiple .gitignore files,
    while collecting traversal statistics.
    """

    def __init__(
        self,
        base_ignore_patterns: Path | str | Iterable[str] | None = None,
        base_ignore_file: Path | str | None = None,
    ):
        """
        Initialize the directory walker with base ignore patterns.

        Args:
            base_ignore_patterns: Base patterns to ignore (applied first).
            base_ignore_file: Path to a file containing base patterns.
        """
        self.base_ignore_patterns = base_ignore_patterns
        self.base_ignore_file = base_ignore_file
        self.stats = WalkStats()

    def walk(
        self,
        root_dir: Path,
        min_depth: int = 0,
        max_depth: int | None = None,
    ) -> Generator[Path, None, None]:
        """
        Walk the directory tree, yielding non-ignored paths.

        Args:
            root_dir: Root directory to start walking from.
            min_depth:
                Skip yielding any files or directories until we reach this depth
                below the root (0 = yield from the root level).
            max_depth:
                Do not descend deeper than this level below the root
                (None or a negative number means no limit).

        Returns:
            Generator yielding Path objects for non-ignored files and directories.

        Raises:
            OSError: If root_dir doesn't exist or is not a directory.
        """
        if not root_dir.exists():
            raise OSError(f"Directory does not exist: {root_dir}")
        if not root_dir.is_dir():
            raise OSError(f"Path is not a directory: {root_dir}")

        # Reset statistics for new walk
        self.stats = WalkStats()

        with get_factory(MatcherImplementation.PURE_PYTHON) as factory:
            # Create a top-level matcher from base patterns or a root-level .gitignore
            root_gitignore = root_dir / ".gitignore"
            parent_matcher = factory.pattern2matcher(
                ignore_file=root_gitignore if root_gitignore.exists() else None,
                base_ignore_patterns=self.base_ignore_patterns,
                base_ignore_file=self.base_ignore_file,
            )

            yield from self._walk_impl(
                current_dir=root_dir,
                root_dir=root_dir,
                current_depth=0,
                matcher=parent_matcher,
                min_depth=min_depth,
                max_depth=max_depth,
            )

            logger.debug(
                f'Walk complete. Ignored: {self.stats.ignored_count}, '
                f'Yielded: {self.stats.yielded_count}'
            )

    def _walk_impl(
        self,
        current_dir: Path,
        root_dir: Path,
        current_depth: int,
        matcher: FileMatcher,
        min_depth: int,
        max_depth: int | None,
    ) -> Generator[Path, None, None]:
        """Internal recursive implementation of the walk."""

        # Handle current directory
        if current_depth >= min_depth and current_dir != root_dir:
            rel_path_str = str(current_dir.relative_to(root_dir))
            if matcher.match(rel_path_str, is_dir=True).matches:
                logger.debug(f'IGNORED DIR: {rel_path_str}')
                self.stats.ignored_count += 1
                return
            yield current_dir
            self.stats.yielded_count += 1

        # Check max depth
        if max_depth is not None and current_depth >= max_depth:
            return

        # Handle local .gitignore
        local_gitignore = current_dir / ".gitignore"
        if current_depth and local_gitignore.exists():
            # TODO
            raise NotImplementedError(f'Found a local .gitignore file at {current_dir}')
        else:
            child_matcher = matcher

        # Process directory contents
        try:
            for entry in current_dir.iterdir():
                rel_path_str = str(entry.relative_to(root_dir))

                # Check if entry should be ignored
                if child_matcher.match(rel_path_str, is_dir=entry.is_dir()).matches:
                    logger.debug(f'IGNORED: {rel_path_str}')
                    self.stats.ignored_count += 1
                    continue

                # Handle directories and files
                if entry.is_dir():
                    yield from self._walk_impl(
                        current_dir=entry,
                        root_dir=root_dir,
                        current_depth=current_depth + 1,
                        matcher=child_matcher,
                        min_depth=min_depth,
                        max_depth=max_depth,
                    )
                elif current_depth + 1 >= min_depth:
                    yield entry
                    self.stats.yielded_count += 1

        except PermissionError:
            return

    @property
    def ignored_count(self) -> int:
        """Number of paths that were ignored during the last walk."""
        return self.stats.ignored_count

    @property
    def yielded_count(self) -> int:
        """Number of paths that were yielded during the last walk."""
        return self.stats.yielded_count

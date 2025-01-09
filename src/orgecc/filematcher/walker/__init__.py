from pathlib import Path
from typing import Generator, Iterable
import logging

from orgecc.filematcher import get_factory, MatcherImplementation, FileMatcher

__all__ = ('walk',)

logger = logging.getLogger(__name__)

def walk(
    root_dir: Path,
    base_ignore_patterns: Path | str | Iterable[str] | None = None,
    base_ignore_file: Path | str | None = None,
    min_depth: int = 0,
    max_depth: int | None = None,
) -> Generator[Path, None, None]:
    """
    Walks a directory tree respecting potentially multiple .gitignore files,
    as well as optional min/max depth constraints.

    Args:
        root_dir: Root directory to start walking from.
        base_ignore_patterns: Base patterns to ignore (applied first).
        base_ignore_file: Path to a file containing base patterns.
        min_depth:
            Skip yielding any files or directories until we reach this depth
            below the root (0 = yield from the root level).
        max_depth:
            Do not descend deeper than this level below the root
            (None or a negative number means no limit).

    Yields:
        Path objects for non-ignored files and directories.
    """

    if not root_dir.exists():
        raise OSError(f"Directory does not exist: {root_dir}")
    if not root_dir.is_dir():
        raise OSError(f"Path is not a directory: {root_dir}")

    ignored_count = 0
    with get_factory(MatcherImplementation.PURE_PYTHON) as factory:
        # Create a top-level matcher from base patterns or a root-level .gitignore, if any
        root_gitignore = root_dir / ".gitignore"
        parent_matcher = factory.pattern2matcher(
            ignore_file=root_gitignore if root_gitignore.exists() else None,
            base_ignore_patterns=base_ignore_patterns,
            base_ignore_file=base_ignore_file,
        )

        # Internal recursive implementation
        def _walk_impl(current_dir: Path, current_depth: int, matcher: FileMatcher):
            nonlocal ignored_count
            # Decide whether to yield the current_dir itself based on depth
            # If current_depth < min_depth, we skip yielding, but still descend
            if current_depth >= min_depth and current_dir != root_dir:
                # Check if current_dir is ignored
                rel_path_str = str(current_dir.relative_to(root_dir))
                if matcher.match(rel_path_str, is_dir=True).matches:
                    logger.debug(f'IGNORED DIR: {rel_path_str}')
                    ignored_count += 1
                    return
                yield current_dir

            # If we have a max_depth limit and we're at it, don't descend further
            if max_depth is not None and current_depth >= max_depth:
                return

            # Attempt to load a local .gitignore if exists in the current dir
            local_gitignore = current_dir / ".gitignore"
            if current_depth and local_gitignore.exists():
                # TODO
                raise NotImplementedError(f'Found a local .gitignore file at {current_dir}')
            else:
                child_matcher = matcher

            # Now iterate sub-entries
            try:
                for entry in current_dir.iterdir():
                    rel_path_str = str(entry.relative_to(root_dir))
                    # Check if entry is ignored
                    if child_matcher.match(rel_path_str, is_dir=entry.is_dir()).matches:
                        logger.debug(f'IGNORED: {rel_path_str}')
                        ignored_count += 1
                        continue

                    # If entry is a directory, recurse
                    if entry.is_dir():
                        yield from _walk_impl(entry, current_depth + 1, child_matcher)
                    else:
                        # Yield file if we're at or beyond min_depth
                        if current_depth + 1 >= min_depth:
                            yield entry
            except PermissionError:
                # Ignore directories we can't access
                return

        yield from _walk_impl(root_dir, 0, parent_matcher)
        logger.warning(f'Ignored count: {ignored_count}')

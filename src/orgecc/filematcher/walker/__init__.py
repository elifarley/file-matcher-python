
from pathlib import Path
from typing import Generator

from orgecc.filematcher import get_factory, MatcherImplementation

__all__ = ('walk',)

def walk(root_dir: Path) -> Generator[Path, None, None]:
    """Walks a directory tree respecting gitignore patterns.

    Traverses the directory tree starting at root_dir, yielding Path objects
    for files and directories that aren't ignored by gitignore patterns.
    Similar to os.walk but with gitignore pattern support.

    Args:
        root_dir: Path object representing the root directory to start walking from.

    Yields:
        Path objects for non-ignored files and directories.

    Raises:
        OSError: If root_dir doesn't exist or permission errors occur.
    """
    # Validate input
    if not root_dir.exists():
        raise OSError(f"Directory does not exist: {root_dir}")
    if not root_dir.is_dir():
        raise OSError(f"Path is not a directory: {root_dir}")

    # Get the matcher factory and create a matcher instance
    with get_factory(MatcherImplementation.PURE_PYTHON) as factory:
        # Look for .gitignore in root directory
        gitignore_path = root_dir / ".gitignore"
        matcher = factory.pattern2matcher(
            ignore_file=gitignore_path if gitignore_path.exists() else None
        )

        def _walk_impl(current_dir: Path) -> Generator[Path, None, None]:
            """Internal implementation of directory walking logic."""
            # Check if the current directory should be ignored
            if current_dir != root_dir:  # Don't check root dir
                rel_path = current_dir.relative_to(root_dir)
                if matcher.match(str(rel_path), is_dir=True).matches:
                    return

            # Process directory contents
            try:
                for entry in current_dir.iterdir():
                    # Get path relative to root for pattern matching
                    rel_path = entry.relative_to(root_dir)

                    # Check if entry should be ignored
                    match_result = matcher.match(
                        str(rel_path),
                        is_dir=entry.is_dir()
                    )

                    if not match_result.matches:
                        yield entry
                        # Recursively walk directories
                        if entry.is_dir():
                            yield from _walk_impl(entry)

            except PermissionError:
                # Skip directories we can't access
                return

        # Start the walk from the root
        yield from _walk_impl(root_dir)

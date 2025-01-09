#!/usr/bin/env python3
"""
Command-line interface for gitignore-aware directory walking.

This module provides a command-line tool for listing files and directories
while respecting gitignore patterns.
"""

from enum import Enum
from pathlib import Path
from typing import Generator, Iterator

import click
from rich.console import Console
from rich.progress import track

from orgecc.filematcher.walker import walk

console = Console()


class OutputFormat(str, Enum):
    """Supported output formats for path display."""
    ABSOLUTE = "absolute"  # Full absolute path
    RELATIVE = "relative"  # Path relative to the root
    NAME = "name"          # Just the file/directory name


class EntryType(str, Enum):
    """Types of filesystem entries to display."""
    ALL = "all"         # Both files and directories
    FILE = "f"          # Files only
    DIRECTORY = "d"     # Directories only


def format_path(
    path: Path,
    root: Path,
    fmt_type: str
) -> str:
    """Format a path according to the specified output format.

    Args:
        path: The path to format
        root: The root directory for relative path calculation
        fmt_type: The desired output format

    Returns:
        Formatted path string
    """
    if fmt_type == OutputFormat.ABSOLUTE:
        return str(path.absolute())
    elif fmt_type == OutputFormat.RELATIVE:
        return str(path.relative_to(root))
    else:  # NAME
        return path.name


def filter_entries(
    paths: Iterator[Path],
    entry_type: str
) -> Generator[Path, None, None]:
    """Filter paths based on entry type.

    Args:
        paths: Iterator of paths to filter
        entry_type: Type of entries to include

    Yields:
        Filtered paths matching the specified entry type
    """
    for path in paths:
        if entry_type == EntryType.ALL:
            yield path
        elif entry_type == EntryType.FILE and path.is_file():
            yield path
        elif entry_type == EntryType.DIRECTORY and path.is_dir():
            yield path


@click.command(help="List files and directories while respecting gitignore patterns.")
@click.argument('path',
                type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path))
@click.option('--type', '-t',
              'entry_type',  # internal name in function => entry_type
              type=click.Choice([e for e in EntryType]),
              default=EntryType.ALL.value,
              help="Type of entries to show")
@click.option('--format', '-f',
              'output_fmt',  # internal name in function => output_fmt
              type=click.Choice([e for e in OutputFormat]),
              default=OutputFormat.RELATIVE.value,
              help="Output format for paths")
@click.option('--null', '-0',
              is_flag=True,
              help="Use null character as separator (useful for xargs)")
@click.option('--quiet', '-q',
              is_flag=True,
              help="Suppress progress and error messages")
# Will be implemented in the future
# @click.option('--follow-symlinks', '-L',
#               is_flag=True,
#               help="Follow symbolic links")

def main(
    path: Path,
    entry_type: str,
    output_fmt: str,
    null: bool,
    quiet: bool,
) -> int:
    """List files and directories while respecting gitignore patterns.

    PATH is the root directory to start walking from.

    Examples:
        file-matcher /path/to/project
        file-matcher /path/to/project --type f --format absolute
        file-matcher /path/to/project --type d --format name
        file-matcher /path/to/project --null | xargs -0 some_command
    """
    try:
        root = path.resolve()
        separator = '\0' if null else '\n'

        # Show a status spinner unless --quiet is used
        with console.status("Scanning files..."):
            # Get all paths from the gitignore-aware walker
            all_paths = walk(root)
            # Filter based on type
            filtered_paths = filter_entries(all_paths, entry_type)
            # Convert to a list for progress tracking or repeated iteration
            paths = list(filtered_paths)

        if not quiet and paths:
            with console.status("Processing entries..."):
                for p in track(paths, description="Processing entries"):
                    formatted_path = format_path(p, root, output_fmt)
                    click.echo(formatted_path, nl=not null)
        else:
            # Direct output without progress tracking
            for p in paths:
                formatted_path = format_path(p, root, output_fmt)
                click.echo(formatted_path, nl=not null)

        return 0

    except KeyboardInterrupt:
        if not quiet:
            console.print("\nOperation cancelled by user", style="yellow")
        return 130
    except Exception as e:
        if not quiet:
            console.print(f"Error: {e}", style="red")
        return 1


if __name__ == '__main__':
    main()

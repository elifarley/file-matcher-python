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
import time
import logging

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
    match fmt_type:
        case OutputFormat.ABSOLUTE:
            return str(path.absolute())
        case OutputFormat.RELATIVE:
            return str(path.relative_to(root))
        case _:  # NAME
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
              'entry_type',
              type=click.Choice([e for e in EntryType]),
              default=EntryType.FILE.value,  # Changed default to FILE
              help="Type of entries to show")
@click.option('--format', '-f',
              'output_fmt',
              type=click.Choice([e for e in OutputFormat]),
              default=OutputFormat.RELATIVE.value,
              help="Output format for paths")
@click.option('--exclude-from', '-X',
              type=click.Path(exists=True, dir_okay=False, path_type=Path),
              help="Base gitignore file to apply before others")
@click.option('--exclude', '-x',
              multiple=True,
              help="Base patterns to ignore (applied before others)")
@click.option('--null', '-0',
              is_flag=True,
              help="Use null character as separator (useful for xargs)")
@click.option('--suppress-errors',
              is_flag=True,
              help="Suppress error messages")
@click.option('--quiet', '-q',
              is_flag=True,
              help="Don't show summary, be quiet")
def main(
    path: Path,
    entry_type: str,
    output_fmt: str,
    exclude_from: Path | None,
    exclude: tuple[str, ...] | None,
    null: bool,
    suppress_errors: bool,
    quiet: bool,
) -> int:
    """List files and directories while respecting gitignore patterns.

    PATH is the root directory to start walking from.

    Examples:
        file-matcher /path/to/project                    # List files only
        file-matcher /path/to/project --type all         # List files and directories
        file-matcher /path/to/project --ignore "*.tmp"   # Ignore .tmp files
        file-matcher /path/to/project --ignore-file extra.gitignore
        file-matcher /path/to/project --null | xargs -0 some_command
    """
    try:
        if not quiet:
            logging.basicConfig(level=logging.WARNING)
        elif suppress_errors:
            logging.basicConfig(level=logging.CRITICAL)
        start_time = time.time()

        root = path.resolve()
        separator = '\0' if null else '\n'

        # Get all paths from the gitignore-aware walker
        all_paths = walk(
            root,
            base_ignore_patterns=exclude,
            base_ignore_file=exclude_from
        )

        # Filter based on type
        entry_count = 0
        # Output paths
        for p in filter_entries(all_paths, entry_type):
            formatted_path = format_path(p, root, output_fmt)
            click.echo(formatted_path, nl=not null)
            entry_count += 1

        if not quiet:
            end_time = time.time()
            duration_s = end_time - start_time
            click.echo(
                f"\nSummary:",
                err=True  # Print summary to stderr to not interfere with piping
            )
            click.echo(f"  Time taken   : {duration_s:5.2f}s", err=True)
            click.echo(f"  Total entries: {entry_count:5d}", err=True)
            click.echo(f"  Entries/s    : {entry_count/duration_s:5.0f}", err=True)
            click.echo(f"--", err=True)
            click.echo(f"  Entry type: {entry_type}", err=True)
            if exclude or exclude_from:
                click.echo("  Exclusions:", err=True)
                if exclude:
                    click.echo(f"    Patterns: {', '.join(exclude)}", err=True)
                if exclude_from:
                    click.echo(f"    File: {exclude_from}", err=True)

        return 0

    except KeyboardInterrupt:
        if not suppress_errors:
            click.echo("\nOperation cancelled by user", err=True, color=True)
        return 130
    except Exception as e:
        if not suppress_errors:
            click.echo(f"Error: {e}", err=True, color=True)
        return 1

if __name__ == '__main__':
    main()

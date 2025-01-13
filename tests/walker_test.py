from typing import Iterable

import pytest
from pathlib import Path
from orgecc.filematcher.walker import DirectoryWalker
from orgecc.filematcher.patterns import new_deny_pattern_source
from orgecc.filematcher import MatcherImplementation, DenyPatternSource

@pytest.fixture
def directory_walker():
    return DirectoryWalker(deny_base=new_deny_pattern_source("ignored_file.txt"))

def test_walk_stats_ignored_count(tmp_path, directory_walker):
    # Create a directory structure with ignored and non-ignored files
    (tmp_path / "file1.txt").touch()
    (tmp_path / "ignored_file.txt").touch()
    (tmp_path / ".gitignore").write_text("ignored_file.txt")

    # Walk the directory
    files = list(directory_walker.walk(tmp_path))

    assert directory_walker.yielded_count == 2
    assert directory_walker.ignored_count == 1
    assert files == [tmp_path / ".gitignore", tmp_path / "file1.txt"]

def test_walk_stats_yielded_count(tmp_path, directory_walker):
    # Create a directory structure with files to be yielded
    (tmp_path / "file1.txt").touch()
    (tmp_path / "file2.txt").touch()

    # Walk the directory
    list(directory_walker.walk(tmp_path))

    # Check if yielded_count is correct
    assert directory_walker.yielded_count == 2  # Includes the directory itself and two files

def test_walk_stats_min_depth(tmp_path, directory_walker):
    # Create a nested directory structure
    (tmp_path / "dir1").mkdir()
    (tmp_path / "dir1" / "file1.txt").touch()

    # Walk the directory with min_depth=1
    files = list(directory_walker.walk(tmp_path, min_depth=1))

    assert files == []
    # Check if only the nested file is yielded
    assert directory_walker.yielded_count == 1

def test_walk_stats_max_depth(tmp_path, directory_walker):
    # Create a nested directory structure
    (tmp_path / "dir1").mkdir()
    (tmp_path / "dir1" / "file1.txt").touch()

    # Walk the directory with max_depth=0
    list(directory_walker.walk(tmp_path, max_depth=0))

    # Check if only the root directory is yielded
    assert directory_walker.yielded_count == 1

def test_walk_stats_permission_error(tmp_path, directory_walker):
    # Create a directory with restricted permissions
    restricted_dir = tmp_path / "restricted_dir"
    restricted_dir.mkdir()
    restricted_dir.chmod(0o000)  # No permissions

    # Walk the directory
    list(directory_walker.walk(tmp_path))

    # Check if stats are unaffected by the permission error
    assert directory_walker.ignored_count == 0
    assert directory_walker.yielded_count == 1  # Only the root directory is yielded

    # Restore permissions for cleanup
    restricted_dir.chmod(0o755)

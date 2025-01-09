from pathlib import Path
from orgecc.filematcher.walker import walk

def test_walk_basic():
    with Path("test_dir").mkdir() as test_dir:
        # Create test files and directories
        test_file = test_dir / "test_file.txt"
        test_file.touch()

        paths = list(walk(test_dir))
        assert len(paths) > 0
        assert test_file in paths

def test_walk_with_gitignore():
    with Path("test_dir").mkdir() as test_dir:
        # Create .gitignore
        gitignore = test_dir / ".gitignore"
        gitignore.write_text("*.txt\n")

        # Create test files
        test_file = test_dir / "test_file.txt"
        test_file.touch()
        test_py = test_dir / "test.py"
        test_py.touch()

        paths = list(walk(test_dir))
        assert test_file not in paths  # Should be ignored
        assert test_py in paths  # Should not be ignored

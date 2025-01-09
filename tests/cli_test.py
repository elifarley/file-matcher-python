from pathlib import Path

from click.testing import CliRunner
from orgecc.filematcher.cli import main

def test_cli_basic():
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create a test directory structure
        Path("test_dir").mkdir()
        Path("test_dir/test_file.txt").touch()

        result = runner.invoke(main, ["test_dir"])
        assert result.exit_code == 0
        assert "test_file.txt" in result.output

def test_cli_type_filter():
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create test directory structure
        Path("test_dir").mkdir()
        Path("test_dir/test_file.txt").touch()
        Path("test_dir/subdir").mkdir()

        # Test files only
        result = runner.invoke(main, ["test_dir", "--type", "f"])
        assert result.exit_code == 0
        assert "test_file.txt" in result.output
        assert "subdir" not in result.output

        # Test directories only
        result = runner.invoke(main, ["test_dir", "--type", "d"])
        assert result.exit_code == 0
        assert "test_file.txt" not in result.output
        assert "subdir" in result.output

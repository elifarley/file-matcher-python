"""
Integration tests for gitignore-like file matching using a corpus of test patterns.

When a file in the corpus directory starts with `x.`, only those "exclusive" files
are tested. Otherwise, all files in the directory are tested.
Thus, prepending corpus files with an `x.` is an easy way to focus on only one or a few tests
that are failing.

Note: Corpus files starting with a dot are never executed. So, if you want to
temporarily hide some corpus tests, just prepend its name with a dot.

Example test failure output explanation:
---------------------------------------
If you see something like this in the test output:

  1. T->F 'build/output.txt'

It indicates that:
- "T->F" means `True` was expected (a match), but `False` was observed (no match).
- `build/output.txt` is the file path tested.

The block of patterns that caused failures will also be printed for easier debugging.
"""

from typing import Generator
import pytest
import re
from pathlib import Path
from enum import Enum, auto
from dataclasses import dataclass

from orgecc.filematcher import get_factory, FileMatcherFactory, FileMatcher, MatcherImplementation, DenyPatternSource
from orgecc.filematcher.patterns import new_deny_pattern_source

# Path to our corpus directory (contains *.txt test files)
CORPUS_DIR = Path(__file__).parent / "corpus"

@pytest.fixture(scope="session")
def file_matcher_factory_native(request) -> FileMatcherFactory:
    """
    Provide a single "native" (that is, one that directly calls the git command) FileMatcherFactory instance
    for all tests in the session.
    """
    factory = get_factory(MatcherImplementation.GIT)
    factory.__enter__()
    request.addfinalizer(lambda: factory.__exit__(None, None, None))
    return factory

@pytest.fixture(scope="session")
def file_matcher_factory_pure_python(request) -> FileMatcherFactory:
    """
    Provide a single pure-Python FileMatcherFactory instance for all tests in the session.

    This fixture uses a Python-only implementation of the matching logic, which is a lot faster than calling git itself.
    """
    factory = get_factory(MatcherImplementation.PURE_PYTHON)
    factory.__enter__()
    request.addfinalizer(lambda: factory.__exit__(None, None, None))
    return factory

class LineType(Enum):
    """
    Represents different types of lines in a `.gitignore`-like corpus file.
    """
    BLOCK_START = auto()
    BLOCK_END = auto()
    PATTERN = auto()
    TEST_CASE = auto()
    COMMENT = auto()
    EMPTY = auto()

@dataclass
class ParsedLine:
    """
    A single parsed line from the corpus, categorized by LineType and containing additional metadata.
    """
    type: LineType
    content: str
    comment: str | None = None
    base_dir: str | None = None
    expected_match: bool | None = None
    path: str | None = None

@dataclass
class IgnoreTestBlock:
    """
    Represents a block of parsed lines from the corpus file.
    """
    base_dir: str
    deny_pattern_source: DenyPatternSource
    test_cases: list[ParsedLine]

    def check_matches(self, file_matcher: FileMatcher) -> list[str]:
        """
        Checks each test case against the file matcher and collects failure messages.

        :param file_matcher: The file matcher to use for checking paths.
        :return: A list of failure messages for test cases that did not match as expected.
        """
        failures = []
        for test in self.test_cases:
            actual = file_matcher.match(test.path)
            comment = test.comment.strip().lstrip('#').strip() if test.comment else ''
            description = f'\n  Rule: {actual.description}' if getattr(actual, 'description', None) else ''
            tf_short = f"{str(test.expected_match)[0]}->{str(actual.matches)[0]}"
            if actual.matches != test.expected_match:
                failures.append(f"{tf_short} '{test.path}' {comment}{description}")
        return failures

def resolve_block(block: list[ParsedLine]) -> IgnoreTestBlock:
    """
    Creates a TestBlock instance from a list of ParsedLine objects.

    Ensures there is exactly one BLOCK_START line per block.
    """
    # Ensure there is exactly one BLOCK_START line
    block_starts = [line for line in block if line.type == LineType.BLOCK_START]
    if len(block_starts) != 1:
        raise ValueError("Each block must contain exactly one BLOCK_START line.")

    block_start = block_starts[0]
    base_dir = block_start.base_dir

    patterns = tuple(line.content for line in block if line.type == LineType.PATTERN)
    test_cases = [line for line in block if line.type == LineType.TEST_CASE]

    return IgnoreTestBlock(base_dir=base_dir, deny_pattern_source=new_deny_pattern_source(patterns), test_cases=test_cases)

class CorpusFileParser:
    """
    Parses the content of a single corpus text file into separate test blocks.

    Each block starts with <.gitignore base='some/path'> and ends with </.gitignore>.
    Inside the block, we have lines for patterns and test cases, and possibly comments.
    """
    def __init__(self, content: str):
        self.lines = content.splitlines()

    @staticmethod
    def parse_line(line: str) -> ParsedLine:
        """
        Parse a single line from a corpus file and categorize it.

        Returns a ParsedLine object with relevant metadata:

        - BLOCK_START lines: <.gitignore base='some/path'>
        - BLOCK_END lines: </.gitignore>
        - PATTERN lines: arbitrary gitignore pattern (no prefix like 't:' or 'f:')
        - TEST_CASE lines: prefixed with 't:' or 'f:' e.g. t:'some/file.txt'
        - COMMENT lines: lines starting with '#'
        - EMPTY lines: blank lines
        """
        stripped = line.rstrip()

        # Empty line
        if not stripped:
            return ParsedLine(LineType.EMPTY, line)

        # Comment line
        if stripped.startswith('#'):
            return ParsedLine(LineType.COMMENT, line)

        # Block start
        if stripped.startswith('<.gitignore'):
            # Attempt to parse out base='...'
            base_start = stripped.find("base='") + len("base='")
            base_end = stripped.find("'>")
            base = stripped[base_start:base_end] if (base_start > 0 and base_end > 0) else ''
            return ParsedLine(LineType.BLOCK_START, line, base_dir=base)

        # Block end
        if stripped.startswith('</'):
            return ParsedLine(LineType.BLOCK_END, line)

        # Test case lines: t:'path' or f:'path'
        if stripped.casefold().startswith(('t:', 'f:')):
            # Determine expected match (True/False)
            prefix = stripped.casefold()[:2]
            if prefix == 't:':
                expected_match = True
            elif prefix == 'f:':
                expected_match = False
            else:
                raise ValueError(f'Invalid test case prefix: {prefix}')

            # Extract the path from the single quotes
            quote_start = line.find("'")
            assert quote_start >= 0, 'Path should be enclosed in single quotes'
            quote_end = line.find("'", quote_start + 1)
            assert quote_end >= 0, 'Unmatched single quote'

            comment = line[quote_end + 1:]
            path = line[quote_start + 1:quote_end]
            return ParsedLine(
                type=LineType.TEST_CASE,
                content=line,
                comment=comment,
                expected_match=expected_match,
                path=path
            )

        # If none of the above, treat as a pattern (possibly with inline comment).
        parts = re.split(r'#(?=(?:[^\']*\'[^\']*\')*[^\']*$)', stripped.replace(r'\#', ''), maxsplit=1)
        pattern = parts[0].rstrip()
        comment = f" #{parts[1]}" if len(parts) > 1 else ""

        return ParsedLine(
            type=LineType.PATTERN,
            content=pattern,
            comment=comment
        )

    def parse_blocks(self) -> Generator[IgnoreTestBlock, None, None]:
        """
        Generates blocks of lines from the file content, one block at a time.

        A block begins at a BLOCK_START line and continues until the next BLOCK_START line or end of file.
        """
        current_block: list[ParsedLine] = []

        for line in self.lines:
            parsed = self.parse_line(line)

            if parsed.type == LineType.BLOCK_START:
                # If we have an open block, yield it before starting a new one.
                if current_block:
                    yield resolve_block(current_block)
                current_block = [parsed]
            elif current_block:  # We are inside a block
                current_block.append(parsed)

        # Yield the last block if it exists.
        if current_block:
            yield resolve_block(current_block)

def get_corpus_blocks() -> list[tuple[str, IgnoreTestBlock]]:
    """
    Returns (test_id, block) tuples for each test block found in all *.txt corpus files
    under the CORPUS_DIR.

    When a file name starts with 'x.', it is considered exclusive. If one or more exclusive files
    exist, then only those files are used. Otherwise, all corpus files are used.

    :returns:
        A tuple of (test_id, block) for each block, where:
            - test_id: a string like "<filename_stem>-#<block_number>"
            - block: a TestBlock instance
    """
    result = []
    # Get all .txt files in corpus dir, excluding hidden files
    files = [f for f in CORPUS_DIR.glob('*.txt')
             if not f.name.startswith('.')]

    # Process each file
    for file in files:
        content = file.read_text(encoding="utf-8")
        parser = CorpusFileParser(content)

        # Parse blocks and create test IDs
        for block_num, block in enumerate(parser.parse_blocks(), 1):
            test_id = f"{file.stem}-#{block_num}"
            result.append((test_id, block))

    # Filter for exclusive tests if present
    exclusive = [(tid, block) for tid, block in result
                 if tid.split('-')[0].casefold().startswith('x.')]

    return exclusive or result

@pytest.mark.parametrize('test_id, block', get_corpus_blocks())
def test_corpus_pure_python(test_id: str, block: IgnoreTestBlock, file_matcher_factory_pure_python: FileMatcherFactory):
    """
    Test each corpus block using the pure-Python FileMatcher.

    This test is parametrized by the `get_corpus_blocks()` generator, so each block
    in each corpus file becomes a separate test invocation.

    Example:
        test_id = "cone-patterns-#1"
        block = TestBlock(base_dir='some/path', patterns=['pattern1', 'pattern2'], test_cases=[ParsedLine(...)])
    """
    _test_corpus(test_id, block, file_matcher_factory_pure_python)

@pytest.mark.parametrize('test_id, block', get_corpus_blocks())
def test_corpus_native(test_id: str, block: IgnoreTestBlock, file_matcher_factory_native: FileMatcherFactory):
    """
    Test each corpus block using the git-based FileMatcher.

    This test is parametrized by the `get_corpus_blocks()` generator, so each block
    in each corpus file becomes a separate test invocation.
    """
    _test_corpus(test_id, block, file_matcher_factory_native)

def _test_corpus(test_id: str, block: IgnoreTestBlock, file_matcher_factory: FileMatcherFactory):
    """
    Runs the actual logic to confirm whether each test case in a block matches
    the patterns as expected.

    The steps are:
    1. Identify the base directory (from the BLOCK_START line).
    2. Extract all pattern lines (PATTERN) into a single list of patterns.
    3. Compile these patterns into a single matcher using the FileMatcherFactory.
    4. For each TEST_CASE line, compare the expected match with the actual match result.
    5. If any mismatches exist, raise a pytest failure with details.
    """
    # Create a file matcher from the patterns
    file_matcher: FileMatcher = file_matcher_factory.pattern2matcher(block.deny_pattern_source)

    # Check matches and collect failures
    failures = block.check_matches(file_matcher)

    # If any failures, create a nice multi-line error message
    if failures:
        failures = [f'{i+1}. {f}' for i, f in enumerate(failures)]
        title = f"Failures: {len(failures)} ({test_id})"
        error_msg = [
            "<.gitignore>",
            *block.deny_pattern_source, # TODO Format correctly
            "</.gitignore>",
            f"\n\n== {title} ==\n",
            *failures
        ]
        pytest.fail('\n'.join(error_msg), pytrace=False)

if __name__ == '__main__':
    # If you run this file directly, pytest is invoked on the module itself.
    pytest.main([__file__, '-v'])

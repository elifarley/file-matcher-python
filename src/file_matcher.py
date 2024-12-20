import fnmatch
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class PatternEntry:
    pattern: str
    flags: int
    original: str
    nowildcard_len: int

class GitIgnore:
    PATTERN_FLAG_NEGATIVE = 1 << 0    # Pattern starts with !
    PATTERN_FLAG_MUSTBEDIR = 1 << 1   # Pattern ends with /
    PATTERN_FLAG_NODIR = 1 << 2       # Pattern has no /

    def __init__(self, patterns: List[str]):
        self.patterns = [self._parse_pattern(p) for p in patterns]

    def _parse_pattern(self, pattern: str) -> PatternEntry:
        flags = 0
        original = pattern

        # Handle negative patterns
        if pattern.startswith('!'):
            flags |= self.PATTERN_FLAG_NEGATIVE
            pattern = pattern[1:]

        # Handle directory-only patterns
        if pattern.endswith('/'):
            flags |= self.PATTERN_FLAG_MUSTBEDIR
            pattern = pattern[:-1]

        # Check if pattern has directory separator
        if '/' not in pattern:
            flags |= self.PATTERN_FLAG_NODIR

        # Calculate non-wildcard prefix length
        nowildcard_len = self._simple_length(pattern)

        return PatternEntry(
            pattern=pattern,
            flags=flags,
            original=original,
            nowildcard_len=nowildcard_len
        )

    def _simple_length(self, pattern: str) -> int:
        """Return length of non-wildcard prefix."""
        for i, c in enumerate(pattern):
            if c in '*?[\\':
                return i
        return len(pattern)

    def _match_pattern(self, pattern: PatternEntry, path: str, is_dir: bool) -> bool:
        """Match a single pattern against a path."""
        # Check directory-only patterns
        if pattern.flags & self.PATTERN_FLAG_MUSTBEDIR and not is_dir:
            return False

        # Handle patterns without directory separator
        if pattern.flags & self.PATTERN_FLAG_NODIR:
            path = path.split('/')[-1]

        # Simple prefix match for non-wildcard part
        if pattern.nowildcard_len > 0:
            if not path.startswith(pattern.pattern[:pattern.nowildcard_len]):
                return False

        # Full pattern match using fnmatch
        return fnmatch.fnmatch(path, pattern.pattern)

    def matches(self, path: str, is_dir: bool = False) -> bool:
        """
        Check if path matches any gitignore pattern.
        Returns True if path should be ignored.
        """
        ignored = False

        for pattern in self.patterns:
            if self._match_pattern(pattern, path, is_dir):
                ignored = not bool(pattern.flags & self.PATTERN_FLAG_NEGATIVE)

        return ignored

# Example usage
def test_gitignore():
    patterns = [
        '*.py[co]',         # Ignore .pyc and .pyo files
        '!important.pyc',   # But don't ignore important.pyc
        'build/',           # Ignore build directory
        '/node_modules',    # Ignore root node_modules
    ]

    gitignore = GitIgnore(patterns)

    test_cases = [
        ('test.pyc', False),
        ('important.pyc', False),
        ('build/output.txt', True),
        ('build', True),
        ('node_modules/package.json', True),
        ('sub/node_modules/file.txt', False),
    ]

    for path, is_dir in test_cases:
        result = gitignore.matches(path, is_dir)
        print(f"{path}: {'ignored' if result else 'not ignored'}")

if __name__ == '__main__':
    test_gitignore()



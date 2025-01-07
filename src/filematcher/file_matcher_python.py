import re

import fnmatch
import os
import logging
from dataclasses import dataclass
from enum import IntFlag, auto
from pathlib import Path
from typing import Generator, Optional
from functools import cached_property, lru_cache
from .file_matcher_api import FileMatcherFactory, FileMatcher, FileMatchResult

logging.basicConfig(level=logging.DEBUG)

@lru_cache(maxsize=512)
def gitignore_syntax_2_fnmatch(
    fnmatch_str_pattern: str, is_anchored: bool = False, is_suffix: bool = False,
    append_slash_or_end: bool = True,
    forced_suffix: str = ''
) -> str | re.Pattern:
    """
    Returns fnmatch_str_pattern itself if the pattern is compatible with .gitignore syntax (that is, fnmatch and .gitignore will give the same results for the pattern).
    This isn't always true, as asterisks have different meaning:
    1. In fnmatch:
      b. '*' means zero or more characters, including '/'
      b. '**' means the same as '*' above
    2. In .gitignore:
      a. '*'  means zero or more characters except for '/'
      b. '**' means zero or more characters, including '/'
    So, if there's at least 1 asterisk, we must return an equivalent re.Pattern
    :param fnmatch_str_pattern:
    :param is_anchored: if the pattern starts with a '/'
    :param is_suffix: Cases like '*.txt'
    :return:
    """
    single_asterisk_count = fnmatch_str_pattern.count('*')
    double_asterisk_count = fnmatch_str_pattern.count('**') if single_asterisk_count > 0 else 0
    single_asterisk_count -= double_asterisk_count * 2
    single_plus_double_asterisk_count = single_asterisk_count + double_asterisk_count
    is_dir_prefix = single_plus_double_asterisk_count == 1 and (fnmatch_str_pattern.endswith('/*') or fnmatch_str_pattern.endswith('/**'))
    if not forced_suffix and (single_plus_double_asterisk_count == 0 or is_dir_prefix or is_suffix):
        # The pattern is compatible with fnmatch, so just return it
        return fnmatch_str_pattern.replace('**', '*')
    pat = fnmatch_str_pattern.replace('**', ';').replace('*', '´')
    pat = (
        fnmatch.translate(pat)
        .replace(';/', '.*').replace(';', '.*')
        .replace(r'´', '[^/]*')
        .replace(r'\Z', '')
    )
    if is_anchored:
        pat = '^' + pat
    else:
        pat = r'(^|/)' + pat
    if forced_suffix:
        pat += forced_suffix
    else:
        if append_slash_or_end:
            pat += r'(/|\Z)'
        else:
            pat += r'\Z'
    print(f'[gitignore_syntax_2_fnmatch] REGEX: {pat}')
    return re.compile(pat)


class PatternFlag(IntFlag):
    """Flags for gitignore pattern types"""
    NONE = 0
    NEGATIVE = auto()      # Pattern starts with !
    MUSTBEDIR = auto()     # Pattern ends with /
    ANCHORED = auto()
    SUFFIX = auto()      # Pattern is a simple suffix (e.g. '*.txt')

@dataclass
class FilePattern(FileMatcher):
    """Represents a single gitignore pattern"""
    base: Path
    # Original pattern before processing
    original: str
    # Processed pattern string (without leading/trailing slash markers)
    pattern: str | re.Pattern
    flags: PatternFlag

    @classmethod
    def from_line(cls, line: str) -> Optional['FilePattern']:
        """Parse a single .gitignore line into a FilePattern object."""
        line = line.rstrip()

        # Skip blank lines and comments
        if not line or line.startswith('#'):
            return None

        original = line
        flags = PatternFlag.NONE

        # Check for leading '!' (negative pattern)
        if line.startswith('!'):
            flags |= PatternFlag.NEGATIVE
            line = line[1:]
        elif line.startswith(r'\!'):
            line = line[1:]


        # Check if pattern is anchored (leading or middle slash)
        if line.startswith('/'):
            flags |= PatternFlag.ANCHORED
            line = line[1:]
        elif '/' in line.rstrip('/'):
            flags |= PatternFlag.ANCHORED

        # Check if pattern ends with '/'
        if line.rstrip('*').endswith('/'):
            flags |= PatternFlag.MUSTBEDIR
            if line.endswith('/'):
                line = line[:-1]

        # Check if it's a simple "endswith" case like '*.txt'
        #    This requires the pattern to start with '*'
        #    but have no other special chars in the remainder.
        if line.startswith('*') and flags & PatternFlag.ANCHORED == 0 and not any(c in line[1:] for c in '*?[\\'):
            flags |= PatternFlag.SUFFIX

        is_suffix = bool(flags & PatternFlag.SUFFIX)
        is_anchored = bool(flags & PatternFlag.ANCHORED)
        return cls(
            base='',
            original=original,
            pattern=gitignore_syntax_2_fnmatch(line, is_anchored, is_suffix),
            flags=flags
        )


    @property
    def is_none(self) -> bool:
        return self.flags == PatternFlag.NONE

    @cached_property
    def nowildcard_len(self) -> int:
        for i, c in enumerate(line):
            if c in '*?[\\':
                return i
        else:
            return -1

    @property
    def is_negative(self) -> bool:
        return bool(self.flags & PatternFlag.NEGATIVE)

    @property
    def is_negative_as_symbol(self) -> str:
        return '!' if self.is_negative else ''

    @property
    def is_anchored(self) -> bool:
        return bool(self.flags & PatternFlag.ANCHORED)

    @property
    def must_be_dir(self) -> bool:
        return bool(self.flags & PatternFlag.MUSTBEDIR)

    @property
    def ends_with(self) -> bool:
        return bool(self.flags & PatternFlag.SUFFIX)

    @property
    def has_wildcard(self) -> bool:
        return self.nowildcard_len < 0

    @property
    def pat_transformed(self) -> re.Pattern | tuple[str, ...]:
        match self.pattern:
            case re.Pattern():
                return self.pattern
        pats: list[str] = [self.pattern]
        if not self.is_anchored:
            pats.append(f'*/{self.pattern}')

        ends_with_slash_asterisks = self.pattern.endswith('/*') or self.pattern.endswith('/**')
        if not ends_with_slash_asterisks:
            pats.append(f'{self.pattern}/*')
            if not self.is_anchored:
                pats.append(f'*/{self.pattern}/*')
        return tuple(pats)

    def match(self, path: str, is_dir: bool=False) -> FileMatchResult:
        match self.pattern:
            case '**', '/**':
                return FileMatchResult(True, f'{self.pattern}', is_dir)
            case '**/', '/**/':
                return FileMatchResult(is_dir, f'{self.pattern}', True)

        path = path.replace('\\', '/')
        # TODO Check
        if not is_dir:
            path = path.rstrip('/')
        elif not path.endswith('/'):
            path += '/'
        _match, description, by_dir = self.prematch(path, self.pat_transformed)

        if _match:
            match self.original:
                case str() as pat:
                    match pat:
                        case pat if pat.endswith('/**/'):
                            main_pat = pat.rstrip('/**/')
                            pat = gitignore_syntax_2_fnmatch(main_pat, is_anchored=True, forced_suffix=r'/[^/]*\Z')
                            if self.prematch(path, pat).matches:
                                msg = f"path isn't inside '{main_pat}'" if path.endswith('/') else f"path isn't a dir"
                                return FileMatchResult(False, f"'{description}' rejected: {msg}", path.endswith('/'))
                            return FileMatchResult(True, description)

            if not is_dir and self.must_be_dir:
                match self.pattern:
                    case re.Pattern():
                        pat = gitignore_syntax_2_fnmatch(self.original.rstrip('/'), append_slash_or_end=False)
                        if pat.search(path):
                            return FileMatchResult(False, f"'{description}' rejected as path isn't a dir")
                    case str() as pat:
                        match pat:
                            case _ if pat.endswith('/*') or pat.endswith('**') or pat.endswith('**/'):
                                ...
                            case _ if fnmatch.fnmatch(path, self.pattern) or fnmatch.fnmatch(path, '*/' + self.pattern):
                                return FileMatchResult(False, f"'{description}' rejected as path isn't a dir")

        return FileMatchResult(_match, description, by_dir)

    def prematch(self, path, pat) -> FileMatchResult:
        _match = False
        description = None
        by_dir = False
        match pat:
            case re.Pattern() as pat:
                _match = bool(pat.search(path))
                description = self.is_negative_as_symbol + str(pat)
                by_dir = not bool(re.compile(pat.pattern.replace(r'(/|\Z)', r'\Z')).search(path))
            case str():
                if fnmatch.fnmatch(path, pat):
                    _match = True
                    description = f"{self.is_negative_as_symbol}'{pat}'"
                    by_dir = pat.endswith('/*')
            case tuple() as pats:
                for pat in pats:
                    if fnmatch.fnmatch(path, pat):
                        _match = True
                        description = f"{self.is_negative_as_symbol}'{pat}'"
                        by_dir = pat.endswith('/*')
                        break
            case _ as invalid:
                raise ValueError(f'Invalid: {invalid}')
        return FileMatchResult(_match, description, by_dir)


class _GitIgnorePythonMatcher(FileMatcher):
    def __init__(self, patterns: tuple[str, ...], base_path: str = "."):
        """
        Initialize GitIgnoreParser with a list of patterns.

        Args:
            patterns: list of gitignore pattern strings.
            base_path: Base directory for relative patterns.
        """
        self.patterns: list[FilePattern] = []
        self.base_path = Path(base_path).resolve()

        for pattern_str in patterns:
            parsed = FilePattern.from_line(pattern_str)
            # Debug: Log the result of parsing each pattern
            logging.debug("[_parse_pattern] '%s' -> %s", pattern_str, parsed)
            if parsed is not None:
                self.patterns.append(parsed)

    def match(self, path: str, is_dir: bool=False) -> FileMatchResult:
        """
        Check if a path should be ignored based on the configured patterns.
        """
        path_is_dir = True if is_dir else path.endswith('/')

        # Last match wins
        _match = None
        for file_pattern in self.patterns:
            result = file_pattern.match(path, path_is_dir)
            if result.matches:
                _match = result._replace(matches=not file_pattern.is_negative)
                if _match.matches and _match.by_dir:
                    _match = _match._replace(description=f"{_match.description} (early stop)")
                    break
        return _match or FileMatchResult(False)

class PurePythonMatcherFactory(FileMatcherFactory):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def pattern2matcher(self, patterns: list[str] | tuple[str, ...]) -> FileMatcher:
        if not isinstance(patterns, tuple):
            patterns = tuple(patterns)  # make hashable for caching
        return self._pattern2matcher(patterns)

    @lru_cache(maxsize=128)
    def _pattern2matcher(self, patterns: tuple[str, ...]) -> _GitIgnorePythonMatcher:
        return _GitIgnorePythonMatcher(patterns)


# Orgecc File Matcher

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![CI](https://github.com/yourusername/file-matcher-python/actions/workflows/test.yml/badge.svg)](https://github.com/yourusername/file-matcher-python/actions/workflows/test.yml)
[![PyPI](https://img.shields.io/pypi/v/orgecc-file-matcher)](https://pypi.org/project/orgecc-file-matcher/)
[![PyPI version](https://badge.fury.io/py/orgecc-file-matcher.svg)](https://pypi.org/project/orgecc-file-matcher/)
[![Python Versions](https://img.shields.io/pypi/pyversions/orgecc-file-matcher.svg)](https://pypi.org/project/orgecc-file-matcher/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A versatile command-line, Python library and toolkit for `.gitignore`-style file matching, designed to meet four key goals:

1. **Pure Python Matcher**: Provide a pure Python implementation that precisely matches Git's behavior.
2. **File Walker**: Traverse directories while respecting `.gitignore` rules at all levels.
3. **Unit Testing**: Verify the correctness of any `.gitignore` matching library or command.
4. **Benchmarking**: Compare the performance of different `.gitignore` matching implementations.

## Features

- **Git-Compatible Matching**: The pure Python matcher passes all test cases, unlike many other libraries.
- **Multiple Implementations**: Choose from pure Python, external libraries ([gitignorefile](https://github.com/excitoon/gitignorefile), [pathspec](https://github.com/excitoon/gitignorefile)), or native Git integration.
- **[Comprehensive Test Suite](#unit-testing)**: Includes a [corpus of test cases](tests/corpus) to validate `.gitignore` matching behavior.
- **Tree-Sitter-Inspired Testing**: The corpus files follow the same rigorous testing principles used by [Tree-Sitter](https://tree-sitter.github.io/tree-sitter/), ensuring high-quality and reliable test coverage.
- **Efficient Directory Traversal**: A file walker that skips ignored files and directories.
- **Cross-Platform**: Works seamlessly on Windows, macOS, and Linux.

## Supported Implementations

See available options in [MatcherImplementation](src/orgecc/filematcher/__init__.py)

- **Pure Python**: No external dependencies. Aims at 100% Git compatibility.
- **Native Git**: Use Git's built-in pattern matching (`git check-ignore -v`) for maximum compatibility. The unit tests are adjusted according to this implementation.
- **External Libraries**: Leverage `gitignorefile` or `pathspec` for enhanced performance.

## Installation

Install via **pip**:

```bash
pip install orgecc-filematcher
```

## Usage

### Pure Python Matcher

Use the Git-compatible pure Python matcher (the default):

```python
from orgecc.filematcher import get_factory, MatcherImplementation

factory = get_factory(MatcherImplementation.PURE_PYTHON)
matcher = factory.pattern2matcher(patterns=["*.pyc", "build/"])
result = matcher.match("path/to/file.pyc")
print(result.matches)  # True or False, matching Git's behavior
```
### File Walker

Traverse directories while respecting `.gitignore` rules:

#### CLI Tool for _macOS_, _Linux_ and _Windows_
You can use the provided command-line tool:


```shell
file-walker --help
```
```
Usage: file-walker [OPTIONS] PATH

  List files and directories while respecting gitignore patterns.

Options:
  -t, --type [all|f|d]            Type of entries to show
  -f, --format [absolute|relative|name]
                                  Output format for paths
  -X, --exclude-from FILE         Base gitignore file to apply before others
  -x, --exclude TEXT              Base patterns to ignore (applied before
                                  others)
  -0, --null                      Use null character as separator (useful for
                                  xargs)
  --suppress-errors               Suppress error messages
  -q, --quiet                     Don't show summary, be quiet
  --help                          Show this message and exit.

```

#### Python Class: _DirectoryWalker_

```python
from orgecc.filematcher.walker import DirectoryWalker

walker = DirectoryWalker()
for file in walker.walk("path/to/directory"):
    print(file)
```

### Unit Testing

Use the included [test corpus](tests/corpus) to validate your `.gitignore` matching implementation.

You can see an example of failure below for the [negation.txt](tests/corpus/negation.txt) test file:

<details>
<summary>Test file: negation.txt [block #7]</summary>


```
<.gitignore>
# ======================
# Advanced Negation & Anchored Patterns
# Demonstrates anchored patterns, directories, and multiple negation layers.
# We test directory handling, anchored patterns, and negation layering:
# ======================

# ignore top-level "build" directory
/build
# unignore a specific file inside that directory
!/build/allow.log

!/dist/allow.log
/dist

# ignore all .tmp files
*.tmp
# unignore a specific top-level file
!/global.tmp

# ignore all .log
*.log
# unignore only *.critical.log
!*.critical.log
</.gitignore>
T: 'build' # is a directory matching /build => ignored
T: 'build/allow.log' unignored, but was first ignored by dir, so still matches
T: 'build/subdir/file.txt' # inside build => ignored
T: 'dist'
T: 'dist/allow.log'
F: 'global.tmp' # unignored by !/global.tmp
T: 'random.tmp' # ignored by '*.tmp'
T: 'some/dir/random.tmp' # also ignored by '*.tmp'
T: 'system.log' # ignored by '*.log'
F: 'kernel.critical.log' # unignored by !*.critical.log
F: 'really.critical.log' # unignored by !*.critical.log
F: 'nested/dir/another.critical.log' # unignored by !*.critical.log
T: 'nested/dir/another.debug.log' # still ignored by '*.log'
```
</details>

<details>
<summary>Test Failure: gitignorefile[negation-#7-block34]</summary>

```
XFAIL tests/filematcher_corpus_test.py::test_corpus_extlib_gitignorefile[negation-#7-block34] - reason:
<.gitignore>
/build
!/build/allow.log
!/dist/allow.log
/dist
*.tmp
!/global.tmp
*.log
!*.critical.log
</.gitignore>


== Failures: 9 (negation-#7) ==

1. T->F 'build' is a directory matching /build => ignored
  Rule: ext-lib: gitignorefile
2. T->F 'build/allow.log' unignored, but was first ignored by dir, so still matches
  Rule: ext-lib: gitignorefile
3. T->F 'build/subdir/file.txt' inside build => ignored
  Rule: ext-lib: gitignorefile
4. T->F 'dist'
  Rule: ext-lib: gitignorefile
5. T->F 'dist/allow.log'
  Rule: ext-lib: gitignorefile
6. T->F 'random.tmp' ignored by '*.tmp'
  Rule: ext-lib: gitignorefile
7. T->F 'some/dir/random.tmp' also ignored by '*.tmp'
  Rule: ext-lib: gitignorefile
8. T->F 'system.log' ignored by '*.log'
  Rule: ext-lib: gitignorefile
9. T->F 'nested/dir/another.debug.log' still ignored by '*.log'
  Rule: ext-lib: gitignorefile

```
</details>

### Benchmarking

Compare the performance of different matcher implementations:

```python
from orgecc.filematcher import get_factory, MatcherImplementation

# Test pure Python implementation
factory = get_factory(MatcherImplementation.PURE_PYTHON)

# Test external library implementation
factory = get_factory(MatcherImplementation.EXTLIB_GITIGNOREFILE)
```

## License

This project is licensed under the Apache 2 License - see the [LICENSE](LICENSE) file for details.


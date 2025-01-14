from importlib.abc import Traversable
from os import PathLike
from pathlib import PurePath, Path
from importlib.resources.abc import Traversable
from typing import TypeAlias

# Type variable for path-like objects
PathLikeOrPurePathOrTraversable: TypeAlias = str | PathLike | PurePath | Traversable

def normalize_path_object(path: PathLikeOrPurePathOrTraversable) -> PurePath | Traversable:
    """
    Normalizes a path-like object into either a `PurePath` or `Traversable` object.

    This function ensures that the input path is converted into a consistent type
    that can be used for further path manipulation or traversal. If the input is
    already a `PurePath` or `Traversable`, it is returned as-is. Otherwise, the
    input is converted into a `Path` object.

    Args:
        path (Union[PathLike, PurePath, Traversable]): The path-like object to normalize.
            This can be a string, `os.PathLike`, `pathlib.PurePath`, or `Traversable`.

    Returns:
        PurePath | Traversable: The normalized path object, either a `PurePath`
        or a `Traversable`.

    Example:
        >>> normalize_path_object("some/path")
        PosixPath('some/path')
        >>> normalize_path_object(PurePath("some/path"))
        PurePath('some/path')
        >>> normalize_path_object(TraversableResource())
        TraversableResource()
    """
    match path:
        case PurePath() | Traversable():
            # If the path is already a PurePath or Traversable, return it as-is
            return path
        case _:
            # For other types (e.g., strings or PathLike), convert to Path
            return Path(path)

def to_purepath(path: PathLikeOrPurePathOrTraversable) -> PurePath:
    match path:
        case PurePath():
            return path
        case Traversable():
           return (path / ' ').parent
    return Path(path)


def relative_to(path: PathLikeOrPurePathOrTraversable, root: PathLikeOrPurePathOrTraversable) -> PurePath:
    """
    Computes the relative path of a path or Traversable object with respect to another path or Traversable object.

    Args:
        path (PathLikeOrPurePathOrTraversable): The object to compute the relative path for.
        root (PathLikeOrPurePathOrTraversable): The root object.

    Returns:
        PurePath: The relative path.

    Raises:
        ValueError: If :path: is not a subdirectory of root.

    Examples:
        >>> from pathlib import PurePath
        >>> root = PurePath("some/directory")
        >>> path = PurePath("some/directory/subdir/file.txt")
        >>> relative_to(path, root)
        PosixPath('subdir/file.txt')

        >>> from importlib.resources import files
        >>> root = files("some_package")
        >>> path = files("some_package.sub_package")
        >>> relative_to(path, root)
        WindowsPath('sub_package')
    """

    match path:
        case PurePath() as pp:
            return pp.relative_to(to_purepath(root))
        case Traversable():
            path = to_purepath(path)
        case _:
            path = normalize_path_object(path)

    match root:
        case PurePath() as pp:
            pass
        case Traversable():
            root = to_purepath(root)
        case _:
            root = normalize_path_object(root)


    # Get the parts of the traversable and root paths
    traversable_parts = path.parts
    root_parts = root.parts

    # Ensure root is a prefix of traversable
    if not traversable_parts[:len(root_parts)] == root_parts:
        raise ValueError(f"{path} is not a subdirectory of {root}")

    # Compute the relative path
    relative_parts = traversable_parts[len(root_parts):]
    return PurePath("/".join(relative_parts))

from importlib.resources.abc import Traversable
from pathlib import PurePath

def relative_to(path: PurePath | Traversable, root: PurePath | Traversable) -> PurePath:
    """
    Computes the relative path of a path or Traversable object with respect to another path or Traversable object.

    Args:
        path (PurePath | Traversable): The object to compute the relative path for.
        root (PurePath | Traversable): The root object.

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
            # TODO Convert root to PurePath if needed
            return pp.relative_to(root)
    # Get the parts of the traversable and root paths
    traversable_parts = path.parts
    match root:
        case str() as str_root:
            # TODO Handle backslashes (WIndows)
            root_parts = str_root.split('/')
        case _:
            root_parts = root.parts

    # Ensure root is a prefix of traversable
    if not traversable_parts[:len(root_parts)] == root_parts:
        raise ValueError(f"{path} is not a subdirectory of {root}")

    # Compute the relative path
    relative_parts = traversable_parts[len(root_parts):]
    return PurePath("/".join(relative_parts))

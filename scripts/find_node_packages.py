#!/usr/bin/env python3
"""
Find ROS package directories that contain a ROS2 node definition and create
soft links to them in a specified output folder.

Usage:
    find_node_packages.py <search_dir> <links_dir> [--max N]

Arguments:
    search_dir  : Root directory to search for ROS packages
    links_dir   : Directory where soft links to packages containing a node will be created
"""

import argparse
import os
import re
import sys

# ---------------------------------------------------------------------------
# Patterns that indicate a ROS2 node definition in Python source files
# ---------------------------------------------------------------------------
# Matches a class that inherits directly from Node (rclpy) or from a qualified
# variant such as rclpy.node.Node or lifecycle_node.LifecycleNode.
_PY_NODE_CLASS_RE = re.compile(
    r"class\s+\w+\s*\(\s*"               # class Foo(
    r"(?:\w+\.)*"                         # optional module qualifiers
    r"(?:Node|LifecycleNode)\s*[,)]",     # Node or LifecycleNode as first base
    re.MULTILINE,
)

# Matches rclpy.create_node(...) — alternative to subclassing
_PY_CREATE_NODE_RE = re.compile(
    r"\brclpy\s*\.\s*create_node\s*\(",
    re.MULTILINE,
)

# Python patterns collected in one list for easy iteration
_PYTHON_NODE_PATTERNS = [_PY_NODE_CLASS_RE, _PY_CREATE_NODE_RE]

# ---------------------------------------------------------------------------
# Patterns that indicate a ROS2 node definition in C/C++ source files
# ---------------------------------------------------------------------------
# Matches class/struct declarations that inherit from rclcpp::Node or
# rclcpp_lifecycle::LifecycleNode, e.g.:
#   class MyNode : public rclcpp::Node {
#   class MyNode : public rclcpp_lifecycle::LifecycleNode
_CPP_NODE_INHERIT_RE = re.compile(
    r":\s*public\s+"
    r"(?:rclcpp(?:_lifecycle)?\s*::\s*)"  # rclcpp:: or rclcpp_lifecycle::
    r"(?:Node|LifecycleNode)\b",
    re.MULTILINE,
)

# Matches direct construction / factory patterns, e.g.:
#   std::make_shared<rclcpp::Node>(...)
#   rclcpp::Node::make_shared(...)
#   new rclcpp::Node(
_CPP_NODE_CONSTRUCT_RE = re.compile(
    r"(?:std\s*::\s*make_shared\s*<\s*rclcpp\s*::\s*(?:Node|LifecycleNode)\s*>"
    r"|rclcpp\s*::\s*(?:Node|LifecycleNode)\s*::\s*make_shared\s*\("
    r"|\bnew\s+rclcpp\s*::\s*(?:Node|LifecycleNode)\s*\()",
    re.MULTILINE,
)

# C++ patterns collected in one list
_CPP_NODE_PATTERNS = [_CPP_NODE_INHERIT_RE, _CPP_NODE_CONSTRUCT_RE]

# File extensions to inspect
_PYTHON_EXTENSIONS = {".py"}
_CPP_EXTENSIONS = {".cpp", ".cxx", ".cc", ".c", ".hpp", ".hxx", ".h"}


def _file_matches_any(path: str, patterns: list) -> bool:
    """Return True if any of *patterns* matches inside *path*."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            content = fh.read()
    except OSError:
        return False
    return any(pat.search(content) for pat in patterns)


def has_ros2_node(directory: str) -> "str | None":
    """
    Return the path of the first file that defines a ROS2 node found inside
    *directory* (searched recursively), or ``None`` if no such file exists.

    Detection heuristics
    --------------------
    Python
      - A class that inherits from ``Node`` or ``LifecycleNode`` (with optional
        module qualifiers such as ``rclpy.node.Node``).
      - A call to ``rclpy.create_node()``.

    C++
      - A class/struct that inherits from ``rclcpp::Node`` or
        ``rclcpp_lifecycle::LifecycleNode`` via ``public`` inheritance.
      - Direct construction via ``std::make_shared<rclcpp::Node>``,
        ``rclcpp::Node::make_shared()``, or ``new rclcpp::Node(``.
    """
    for dirpath, dirnames, filenames in os.walk(directory, followlinks=True):
        # Prune test directories so os.walk never descends into them
        dirnames[:] = [d for d in dirnames if d.lower() not in ("test", "tests")]
        for filename in filenames:
            ext = os.path.splitext(filename)[1].lower()
            filepath = os.path.join(dirpath, filename)
            if ext in _PYTHON_EXTENSIONS:
                if _file_matches_any(filepath, _PYTHON_NODE_PATTERNS):
                    return filepath
            elif ext in _CPP_EXTENSIONS:
                if _file_matches_any(filepath, _CPP_NODE_PATTERNS):
                    return filepath
    return None


# ---------------------------------------------------------------------------
# Package-discovery helpers (mirrors find_missing_readme.py style)
# ---------------------------------------------------------------------------

def parent_is_test_dir(directory: str) -> bool:
    """Return True if the immediate parent directory is named 'test' or 'tests'."""
    parent = os.path.basename(os.path.dirname(os.path.abspath(directory)))
    return parent.lower() in ("test", "tests")


def find_node_packages(search_dir: str):
    """
    Walk the directory tree rooted at *search_dir* and yield ``(pkg_path,
    node_file)`` tuples for ROS package directories (containing ``package.xml``)
    that:

    * are not inside a ``test`` / ``tests`` parent directory, and
    * contain at least one ROS2 node definition.

    ``node_file`` is the absolute path of the first source file detected as
    defining a node.
    """
    for dirpath, _dirnames, filenames in os.walk(search_dir, followlinks=True):
        if "package.xml" in filenames:
            if not parent_is_test_dir(dirpath):
                node_file = has_ros2_node(dirpath)
                if node_file is not None:
                    yield os.path.abspath(dirpath), node_file


def make_safe_link_name(target_path: str, links_dir: str) -> str:
    """
    Generate a unique soft-link name inside *links_dir* for *target_path*.
    Uses the package directory basename; appends a numeric suffix on collision.
    """
    base = os.path.basename(target_path)
    candidate = os.path.join(links_dir, base)
    if not os.path.lexists(candidate):
        return candidate
    counter = 1
    while True:
        candidate = os.path.join(links_dir, f"{base}_{counter}")
        if not os.path.lexists(candidate):
            return candidate
        counter += 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description=(
            "Find ROS packages that define a ROS2 node and create soft links "
            "to them in the specified links directory."
        )
    )
    parser.add_argument(
        "search_dir",
        help="Root directory to search for ROS packages.",
    )
    parser.add_argument(
        "links_dir",
        help="Directory in which to place soft links to packages containing a node.",
    )
    parser.add_argument(
        "--max",
        type=int,
        default=None,
        metavar="N",
        help="Stop after finding N packages (default: no limit).",
    )
    args = parser.parse_args()

    search_dir = os.path.abspath(args.search_dir)
    links_dir = os.path.abspath(args.links_dir)

    if not os.path.isdir(search_dir):
        print(f"Error: search directory does not exist: {search_dir}", file=sys.stderr)
        sys.exit(1)

    os.makedirs(links_dir, exist_ok=True)

    count = 0
    for pkg_path, node_file in find_node_packages(search_dir):
        link_path = make_safe_link_name(pkg_path, links_dir)
        os.symlink(pkg_path, link_path)
        pkg_name = os.path.basename(link_path)
        rel_node_file = os.path.relpath(node_file, pkg_path)
        print(f"{pkg_name}  [{rel_node_file}]")
        count += 1
        if args.max is not None and count >= args.max:
            break

    print(f"\nFound {count} package(s) with ROS2 node definitions.", file=sys.stderr)


if __name__ == "__main__":
    main()

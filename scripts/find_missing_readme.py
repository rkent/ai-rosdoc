#!/usr/bin/env python3
"""
Find ROS package directories that are missing a README file and create
soft links to them in a specified output folder.

Usage:
    find_missing_readme.py <search_dir> <links_dir>

Arguments:
    search_dir  : Root directory to search for ROS packages
    links_dir   : Directory where soft links to packages without README will be created
"""

import argparse
import os
import sys


def has_readme(directory: str) -> bool:
    """Return True if the directory contains any file matching README.* (case-insensitive)."""
    try:
        for entry in os.scandir(directory):
            if entry.is_file() and entry.name.upper().startswith("README"):
                # Must be README.* (i.e. README followed by a dot and extension),
                # or exactly "README" with no extension also counts as README.*
                name = entry.name.upper()
                if name == "README" or name.startswith("README."):
                    return True
    except PermissionError:
        pass
    return False


def parent_is_test_dir(directory: str) -> bool:
    """Return True if the immediate parent directory is named 'test' or 'tests'."""
    parent = os.path.basename(os.path.dirname(os.path.abspath(directory)))
    return parent.lower() in ("test", "tests")


def find_packages_without_readme(search_dir: str):
    """
    Walk the directory tree rooted at search_dir and yield paths of ROS package
    directories (containing package.xml) that have no README file and whose
    parent is not named 'test' or 'tests'.
    """
    for dirpath, dirnames, filenames in os.walk(search_dir, followlinks=True):
        if "package.xml" in filenames:
            if not parent_is_test_dir(dirpath) and not has_readme(dirpath):
                yield os.path.abspath(dirpath)
            # Don't descend into sub-packages (a package.xml in a child would be
            # a nested package — keep walking to discover them too by NOT pruning).


def make_safe_link_name(target_path: str, links_dir: str) -> str:
    """
    Generate a unique soft-link name inside links_dir for the given target_path.
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


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Find ROS packages without a README file and create soft links "
            "to them in the specified links directory."
        )
    )
    parser.add_argument(
        "search_dir",
        help="Root directory to search for ROS packages.",
    )
    parser.add_argument(
        "links_dir",
        help="Directory in which to place soft links to packages missing a README.",
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

    found = 0
    for package_dir in find_packages_without_readme(search_dir):
        link_path = make_safe_link_name(package_dir, links_dir)
        os.symlink(package_dir, link_path)
        print(f"Linked: {link_path} -> {package_dir}")
        found += 1
        if args.max is not None and found >= args.max:
            print(f"Reached maximum of {args.max} package(s); stopping search.")
            break

    if found == 0:
        print("No ROS packages without a README were found.")
    else:
        print(f"\nTotal: {found} package(s) linked in {links_dir}")


if __name__ == "__main__":
    main()

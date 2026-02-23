# Instructions: find_node_packages.py

## Purpose

Find ROS package directories that contain ROS nodes, and create a soft link to each such directory inside a specified output folder.

## Script location

`scripts/find_node_packages.py`

The script should be made executable (`chmod +x`).

## Command-line interface

```
find_node_packages.py <search_dir> <links_dir> [--max N]
```

| Argument | Type | Description |
|---|---|---|
| `search_dir` | positional | Root directory to search for ROS packages. |
| `links_dir` | positional | Directory in which to place soft links to packages containing a node. Created automatically if it does not exist. |
| `--max N` | optional | Stop after finding N packages. If omitted, search continues until all packages are found. |

## ROS package detection

A directory is considered a ROS package if it directly contains a file named `package.xml`.

## Exclusions

Exclude a package directory if either of the following is true:

1. Its immediate parent directory is named `test` or `tests` (case-insensitive comparison).
2. It does not contain a ROS node (see definition below).
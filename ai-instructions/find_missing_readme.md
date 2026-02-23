# Instructions: find_missing_readme.py

Write a Python script placed in a subdirectory `scripts/` of the workspace with the following behaviour.

## Purpose

Find ROS package directories that do not contain a README file, and create a soft link to each such directory inside a specified output folder.

## Script location

`scripts/find_missing_readme.py`

The script should be made executable (`chmod +x`).

## Command-line interface

```
find_missing_readme.py <search_dir> <links_dir> [--max N]
```

| Argument | Type | Description |
|---|---|---|
| `search_dir` | positional | Root directory to search for ROS packages. |
| `links_dir` | positional | Directory in which to place soft links to packages missing a README. Created automatically if it does not exist. |
| `--max N` | optional | Stop after finding N packages. If omitted, search continues until all packages are found. |

## ROS package detection

A directory is considered a ROS package if it directly contains a file named `package.xml`.

## Exclusions

Exclude a package directory if either of the following is true:

1. Its immediate parent directory is named `test` or `tests` (case-insensitive comparison).
2. It already contains a README file (see definition below).

## README file definition

A README file is any file in the package directory whose name, compared case-insensitively, is either:
- exactly `README`, or
- starts with `README.` (i.e. has an extension such as `.md`, `.rst`, `.txt`, etc.).

## Directory traversal

- Use `os.walk` starting from `search_dir`.
- **Follow symbolic links** to directories during traversal (`followlinks=True`).
- Continue descending into sub-directories even after finding a `package.xml` (to allow discovering nested packages).

## Soft link creation

- For each qualifying package directory, create a soft link inside `links_dir` pointing to the absolute path of the package directory.
- The link name is the basename of the package directory.
- If a name collision occurs in `links_dir`, append a numeric suffix (`_1`, `_2`, …) until a unique name is found (`os.path.lexists` check).

## Output

- Print each link created: `Linked: <link_path> -> <package_dir>`
- If `--max N` is reached, print: `Reached maximum of N package(s); stopping search.`
- If no packages are found, print: `No ROS packages without a README were found.`
- Otherwise, print a summary: `Total: N package(s) linked in <links_dir>`

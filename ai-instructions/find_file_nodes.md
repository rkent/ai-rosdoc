# Instructions: find_file_nodes.py

Write a Python script placed in a subdirectory `scripts/` of the workspace with the following behaviour.

## Purpose

Find ROS package directories that contain ROS 2 node definitions and write a JSON file that lists each such package along with the specific source file in which the node was detected. The JSON file is designed to be consumed by a documentation-generation step that needs to know exactly which files to read, without having to re-scan the entire source tree.

## Script location

`scripts/find_file_nodes.py`

The script should be made executable (`chmod +x`).

## Command-line interface

```
find_file_nodes.py <search_dir> <output_json> [--max N]
```

| Argument | Type | Description |
|---|---|---|
| `search_dir` | positional | Root directory to search for ROS packages. |
| `output_json` | positional | Path of the JSON file to write. If the path does not already end with `.json`, the suffix is appended automatically. Parent directories are created automatically if they do not exist. |
| `--max N` | optional | Stop after finding N packages with nodes. If omitted, search continues until all packages are found. |

## ROS package detection

A directory is considered a ROS package if it directly contains a file named `package.xml`.

## Exclusions

Exclude a package directory if either of the following is true:

1. Any component of its path (after `search_dir`) is named `test` or `tests` (case-insensitive comparison).
2. No ROS 2 node definition is found in its source files (see node detection rules below).

## Node detection rules

These rules are the same as those in `find_node_packages.py`.

### Python files (`.py`)

A Python file is considered to define a node if it matches any of the following patterns:

- A class that directly inherits from `Node` or `LifecycleNode`, with optional module qualifiers and allowing both single and multiple inheritance:
  ```
  class Foo(Node ...
  class Foo(rclpy.node.Node ...
  class Foo(LifecycleNode ...
  ```
- A call to `rclpy.create_node(`.

### C/C++ files (`.cpp`, `.hpp`, `.h`, `.cc`, `.cxx`)

A C/C++ file is considered to define a node if it matches any of the following patterns:

- A class or struct that inherits publicly from `rclcpp::Node` or `rclcpp_lifecycle::LifecycleNode`:
  ```
  class Foo : public rclcpp::Node
  class Foo : public rclcpp_lifecycle::LifecycleNode
  ```
- Direct construction patterns:
  ```
  std::make_shared<rclcpp::Node>(
  rclcpp::Node::make_shared(
  new rclcpp::Node(
  ```

### Test directory pruning

When walking a package directory looking for a node file, prune subdirectories named `test` or `tests` (case-insensitive) from the walk so that test code does not trigger a false positive.

## Output JSON format

The output is a JSON array. Each element is an object with the following fields:

| Field | Type | Description |
|---|---|---|
| `package` | string | The basename of the package directory (i.e. the ROS package name). |
| `package_dir` | string | Absolute path to the package directory (the directory that contains `package.xml`). |
| `node_files` | array of strings | Paths to **all** source files in which a node definition was detected, each expressed as a path **relative to `package_dir`**, in `os.walk` discovery order. |

### Example

```json
[
  {
    "package": "twist_stamper",
    "package_dir": "/srv/repos/rolling/twist_stamper",
    "node_files": [
      "twist_stamper/twist_stamper.py",
      "twist_stamper/twist_unstamper.py"
    ]
  },
  {
    "package": "rosbag2_transport",
    "package_dir": "/srv/repos/rolling/rosbag2/rosbag2_transport",
    "node_files": [
      "src/rosbag2_transport/recorder.cpp",
      "src/rosbag2_transport/player.cpp"
    ]
  }
]
```

### Ordering

Entries should appear in the order in which the packages were discovered during the directory walk.

## Directory traversal

- Use `os.walk` starting from `search_dir`.
- **Follow symbolic links** to directories during traversal (`followlinks=True`).
- When a `package.xml` is found, descended into sub-directories is allowed (to handle nested packages), but the sub-directories named `test` or `tests` are pruned for the *package-level* node-detection walk (not for the top-level package-discovery walk).

## Soft links

This script does **not** create any soft links. That is the job of `find_node_packages.py`.

## Output (console)

- For each package added to the JSON, print one line per detected node file:
  ```
  <package_name>  [<node_file>]
  ```
  where `<node_file>` is the path relative to the package directory, matching an entry in the `node_files` array stored in the JSON.
- If `--max N` is reached, print:
  ```
  Reached maximum of N package(s); stopping search.
  ```
- After writing the JSON file, print a summary line:
  ```
  Total: N package(s) written to <output_json>
  ```
- If no qualifying packages are found, print:
  ```
  No ROS packages containing a node were found.
  ```

## Relationship to other scripts

| Script | Output |
|---|---|
| `find_node_packages.py` | Creates symlinks to package directories |
| `find_file_nodes.py` | Creates a JSON file listing packages and all node-defining source files found in each |

The JSON file produced by `find_file_nodes.py` is intended to be passed to a documentation-generation tool (such as a modified version of `generate-node-docs`) so that the tool can read directly from the identified source files without re-scanning the entire repository.

---
name: Document Node Files
description: Generate or update node documentation from a JSON index produced by find_file_nodes.py.
agent: 'agent'
---

## Inputs

This prompt requires one argument: the path to a JSON index file produced by `scripts/find_file_nodes.py`. The JSON file is a array of objects with the following fields:

- `package` — the ROS package name
- `package_dir` — absolute path to the directory that contains `package.xml`
- `node_files` — list of source file paths (relative to `package_dir`) in which node definitions were detected

If no path is supplied, look for a JSON file in the current working directory whose name ends in `.json` and which contains the expected array structure.

## Step 1 — Read source files and identify nodes

For each package in the JSON array, read the files listed in `node_files` (as absolute paths constructed from `package_dir` + the relative path). These are the primary files to read.

**IMPORTANT: To avoid permission dialog requests when reading files outside the workspace, use terminal commands (e.g. `cat`, `grep`) via `run_in_terminal` instead of file read tools. This prevents VS Code from requesting file access permissions.**

If those files alone do not provide enough information to fully document a node (e.g. the class body is in a separate `.cpp` implementation file, parameters are declared in a utility header, or entry point names are in `setup.py` / `CMakeLists.txt`), read the additional files needed. Limit supplementary reads to files that are directly referenced (e.g. `#include` directives, Python imports) or that have standard names in the package (`setup.py`, `CMakeLists.txt`, `package.xml`).

Identify all nodes defined across the listed files. A single source file may define more than one node class.

## Step 2 — Write documentation

The documentation should be in a folder `Nodes/<package name>/` relative to the directory from which this prompt is invoked — NOT relative to the package directory or any subdirectory of it. There should be one `.md` markdown file per node, with the name of the file matching the node name. Documentation for each node should include:

- node name
- after the node name, in italics: *This file is ai generated and may contain mistakes. If you edit this file, remove this notice to prevent rewriting by ai.*
- node description
- subscriptions, publishers, services, and actions for the node with interface (e.g. message) type
- **IMPORTANT: ONLY include sections (## Publishers, ## Subscribers, ## Services, ## Actions) if the node actually has items of that type. DO NOT include empty sections or sections with "None". Omit the entire section if there are no items.**
- documentation of any parameters defined for the node
- example of how to run the node using the `ros2 run` command

Additional instructions for the markdown file:
- If a default value is a C++ constant or macro, find the literal value of that constant — do not just show the constant name.
- If an `.md` file already exists for a node, read it and compare it against the current source code. Update any fields that are inaccurate or incomplete. However, if the file contains the text "file is ai generated", do not modify it regardless of accuracy.

## Step 3 — Write JSON documentation files

In addition to the markdown file, create a `.json` file in the same `Nodes/<package name>/` directory (relative to the prompt invocation directory, not the package directory), with the name of the file matching the node name. The json file should match the following schema per https://json-schema.org/draft/2020-12/schema:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "http://ros.org/schemas/node_doc.json",
  "donotmodify": "false",
  "name": {
    "type": "string",
    "description": "node name"
  },
  "summary": {
    "type": "string",
    "description": "a short description of the function of the node",
    "minLength": 30,
    "maxLength": 100
  },
  "overview": {
    "type": "string",
    "description": "a longer description of the function of the node",
    "minLength": 110,
    "maxLength": 300
  },
  "repo": {
    "type": "string",
    "description": "the name of the repository containing the node's package"
  },
  "package": {
    "type": "string",
    "description": "the name of the package containing the node"
  },
  "parameters": {
    "type": "array",
    "description": "ROS parameters for the node",
    "items": {
      "type": "object",
      "properties": {
        "name": {
          "type": "string",
          "description": "the identifier used to reference the parameter in the ROS API"
        },
        "type": {
          "type": "string",
          "description": "the type of the parameter, e.g. string, int, float"
        },
        "default": {
          "type": "string",
          "description": "the default value of the parameter, if any"
        },
        "summary": {
          "type": "string",
          "description": "a short description of the purpose of the parameter",
          "minLength": 20,
          "maxLength": 80
        }
      }
    }
  },
  "interfaces": {
    "type": "array",
    "description": "A list of the various interfaces implemented by the node",
    "items": {
      "type": "object",
      "properties": {
        "itype": {
          "enum": ["publisher", "subscriber", "service", "client", "action server", "action client"],
          "description": "The type of ROS interface"
        },
        "topic": {
          "type": "string",
          "description": "the string used to reference the interface"
        },
        "mtype": {
          "type": "string",
          "description": "the message type that characterizes the interface"
        },
        "summary": {
          "type": "string",
          "description": "A short summary of the purpose of the interface",
          "minLength": 20,
          "maxLength": 80
        }
      }
    }
  }
}
```

If the `.json` file already exists and contains a top-level field `"donotmodify"` with the value `"true"`, do not change it. Otherwise, read the existing file and update it if needed to reflect the correct current values.

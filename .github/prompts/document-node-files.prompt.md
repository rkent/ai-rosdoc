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

## Step 0 — Initialize local temporary directory

Create a `./tmp` directory in the current workspace if it doesn't exist. Use this directory for all temporary files instead of `/tmp` to avoid permission dialog requests.

## Step 1 — Batch nodes into groups of 10

Analyze the JSON input and group all nodes by package. Create a list of batches where each batch contains up to 10 nodes with their package information. Store this batch list in `./tmp/node_batches.json`.

**Subagent Task Delegation:**
For each batch, invoke a subagent with the following instruction. Do NOT wait for detailed responses or maintain extensive back-and-forth interaction:

```
You are responsible for documenting a batch of ROS2 nodes and writing their markdown and JSON files.

Input batch (JSON): [BATCH_DATA]

For each node in this batch:
1. Use terminal commands to read source files from /srv/repos/rolling and workspace files
2. Extract node definitions, interfaces (publishers/subscribers/services), and parameters
3. Generate markdown file: Nodes/<package>/<node>.md with template:
   - Node name, ai-generated notice, description
   - Only include Publisher/Subscriber/Service/Action sections if populated
   - Parameters with defaults and types
   - Example: ros2 run <package> <node>
4. Generate JSON file: Nodes/<package>/<node>.json matching http://ros.org/schemas/node_doc.json schema:
   - name, summary (30-100 chars), overview (110-300 chars)
   - repo, package, parameters, interfaces arrays
5. Use mkdir -p for directory creation
6. Return single line: "BATCH_COMPLETE: X nodes documented in Y packages"

Work autonomously. Minimize output. No intermediate feedback needed.
```

Collect results from each subagent batch task. Only report summary statistics once all batches complete.

## Step 2 — Read source files and identify nodes (Subagent Task)

For each node in the batch, read the files listed in `node_files` (as absolute paths constructed from `package_dir` + the relative path). These are the primary files to read.

**IMPORTANT: To avoid permission dialog requests when reading files outside the workspace, use terminal commands (e.g. `cat`, `grep`) via `run_in_terminal` instead of file read tools. This prevents VS Code from requesting file access permissions.**

**IMPORTANT: Do not try to write to the /tmp directory. Use the `./tmp` directory in the current workspace for any temporary files needed during processing.**

If those files alone do not provide enough information to fully document a node (e.g. the class body is in a separate `.cpp` implementation file, parameters are declared in a utility header, or entry point names are in `setup.py` / `CMakeLists.txt`), read the additional files needed. Limit supplementary reads to files that are directly referenced (e.g. `#include` directives, Python imports) or that have standard names in the package (`setup.py`, `CMakeLists.txt`, `package.xml`).

Identify all nodes defined across the listed files. A single source file may define more than one node class.

## Step 3 — Write documentation (Subagent Task)

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

## Step 4 — Write JSON documentation files (Subagent Task)

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


## Step 5 — Consolidate Results and Report Summary

After all subagent batches have completed:

1. Count total nodes documented across all batches
2. Count total packages touched
3. Update or create `./tmp/documentation_manifest.json` with:
   - timestamp of completion
   - total_batches_processed
   - total_nodes_documented
   - total_packages_processed
   - batch_results (array of completion messages)
4. Report final summary: "**DOCUMENTATION COMPLETE:** X nodes documented across Y packages in Z batches"

This final step ensures visibility into the complete documentation run without maintaining excessive context about individual batch details.

````

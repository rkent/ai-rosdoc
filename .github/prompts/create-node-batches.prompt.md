````prompt
---
name: Create Node Batches
description: Read a JSON node index and write batch files to ./tmp for later subagent processing.
agent: 'agent'
---

## Inputs

This prompt requires one argument: the path to a JSON index file produced by `scripts/find_file_nodes.py`. The JSON file is an array of objects with the following fields:

- `package` — the ROS package name
- `package_dir` — absolute path to the directory that contains `package.xml`
- `node_files` — list of source file paths (relative to `package_dir`) in which node definitions were detected

If no path is supplied, look for a JSON file in the current working directory whose name ends in `.json` and which contains the expected array structure.

## Step 0 — Initialize local temporary directory

Create a `./tmp` directory in the current workspace if it doesn't exist. Use this directory for all temporary files instead of `/tmp` to avoid permission dialog requests.

## Step 1 — Create batch files

Analyze the JSON input and group entries by package. Create batches of up to 10 entries each. For each batch N (1-based, zero-padded to 3 digits), write the batch array to `./tmp/batch_NNN.json`.

After writing all batch files, report:
- The total number of batch files created (e.g. `BATCHES_CREATED: 42`)
- The range of batch numbers (e.g. `BATCH_RANGE: 001–042`)
````

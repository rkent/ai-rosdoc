# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

This repository contains AI-assisted tooling for generating and maintaining documentation for ROS 2 (Robot Operating System 2) packages and nodes. The workflow scans ROS workspaces to identify packages/nodes and then uses AI prompts to produce structured documentation (Markdown + JSON).

## Repository Structure

- `scripts/` — Python scripts for scanning ROS workspaces
- `ai-instructions/` — Natural-language specifications from which the scripts were generated
- `.github/prompts/` — GitHub Copilot agent prompt files that drive AI documentation generation
- `demos/` — Example output from documentation runs (gitignored by default)

## Scripts

All scripts in `scripts/` are standalone Python 3 executables with no external dependencies beyond the standard library.

### `scripts/find_file_nodes.py`

Scans a ROS workspace and produces a JSON index of every package that contains a ROS 2 node definition. This JSON file is the primary input to the documentation-generation step.

```bash
python3 scripts/find_file_nodes.py <search_dir> <output_json> [--max N]
# Example:
python3 scripts/find_file_nodes.py /srv/repos/rolling nodes_index.json
```

### `scripts/find_node_packages.py`

Scans a ROS workspace and creates symlinks to packages that contain node definitions, useful for inspecting them in a flat directory.

```bash
python3 scripts/find_node_packages.py <search_dir> <links_dir> [--max N]
```

### `scripts/find_missing_readme.py`

Scans a ROS workspace and creates symlinks to packages that are missing a README file.

```bash
python3 scripts/find_missing_readme.py <search_dir> <links_dir> [--max N]
```

## Node Detection Heuristics

All three scripts share the same detection logic:

- **Python**: class inheriting from `Node` or `LifecycleNode`; or a call to `rclpy.create_node()`
- **C++**: class inheriting publicly from `rclcpp::Node` or `rclcpp_lifecycle::LifecycleNode`; or direct construction via `std::make_shared<rclcpp::Node>`, `rclcpp::Node::make_shared()`, or `new rclcpp::Node(`
- Directories named `test` or `tests` are always pruned/excluded

## AI Prompt Workflows

### Generate Node Documentation (`.github/prompts/generate-node-docs.prompt.md`)

Agent prompt that reads node source files and writes one `.md` + one `.json` file per node into `Nodes/<package_name>/` relative to the directory from which the prompt is invoked.

The JSON schema captures: `name`, `summary` (30–100 chars), `overview` (110–300 chars), `repo`, `package`, `parameters[]`, and `interfaces[]` (with `itype` enum: publisher/subscriber/service/client/action server/action client).

Key rule: **only include interface sections (Publishers, Subscribers, etc.) if the node actually has items of that type**. Do not write empty sections.

If a file already contains `"file is ai generated"` (markdown) or `"donotmodify": "true"` (JSON), do not overwrite it.

### Update Package README (`.github/prompts/update-package-readme.prompt.md`)

Agent prompt that writes or updates `README.md` for each ROS 2 package in the current directory. Only touches files that either don't exist or already contain the text `'ai generated'`. Includes msg/srv/action definitions, dependencies (for meta-packages only), and brief node summaries (not full interface details).

## Typical End-to-End Workflow

1. Run `find_file_nodes.py` against a ROS workspace to produce a JSON index.
2. Invoke the `generate-node-docs` Copilot agent prompt from the desired output directory, pointing it at the source workspace (it reads from the JSON index internally or re-scans).
3. Optionally run `find_missing_readme.py` to identify packages still needing READMEs, then invoke the `update-package-readme` prompt.

## Output Conventions

- Node docs: `Nodes/<package_name>/<node_name>.md` and `Nodes/<package_name>/<node_name>.json`
- The `demos/` directory holds reference outputs from prior runs (committed selectively; `demos/rolling-noreadme/` is gitignored)
- C++ default parameter values should resolve constants to their literal values, not just show the constant name

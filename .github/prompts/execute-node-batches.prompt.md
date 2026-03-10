````prompt
---
name: Execute Node Batches
description: Run document-node-batch subagents over a specified range of batch files in ./tmp.
agent: 'agent'
---

## Inputs

This prompt requires three arguments specifying the range of batch files to process:

- `BATCH_START` — first batch number to process (1-based, e.g. `1`)
- `BATCH_END` — last batch number to process (inclusive, e.g. `42`)
- `BATCH_ROOT` (optional) — directory in which batch files are located; defaults to `./tmp`

If these are not provided, ask.

The workspace root is the current working directory unless explicitly provided.

## Step 1 — Invoke subagents in parallel

For each batch number N in the range [BATCH_START, BATCH_END], zero-padded to 3 digits:

1. Verify that `./tmp/batch_NNN.json` exists; skip with a warning if it does not.
2. Invoke a subagent with the following instruction. Do NOT wait for detailed responses or maintain extensive back-and-forth interaction. Launch all subagents in parallel:

```
Follow the instructions in `.github/prompts/document-node-batch.prompt.md`.
The input batch data is in [BATCH_FILE_PATH].
The workspace root is [WORKSPACE_ROOT].
```

Collect the `BATCH_COMPLETE` result lines from each subagent. Only report summary statistics once all batches complete.

## Step 2 — Consolidate Results and Report Summary

1. Count total nodes documented across all batches
2. Count total packages touched
3. Update or create `./tmp/documentation_manifest.json` with:
   - timestamp of completion
   - total_batches_processed
   - total_nodes_documented
   - total_packages_processed
   - batch_results (array of completion messages)
4. Report final summary: "**DOCUMENTATION COMPLETE:** X nodes documented across Y packages in Z batches"
````

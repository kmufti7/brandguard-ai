---
state: VERIFIED
timestamp: 2026-05-12T00:19:32.107401+00:00
brief: scripts/doc_pipeline/briefs/usage.brief.md
mode: encoded
plugin_command: 
framework: 
word_count_floor: 600
---

# USAGE

BrandGuard AI is a governed marketing AI system that filters campaign copy against brand and legal guardrails. This guide covers the standard workflows for running the system end to end, evaluating its performance, and validating its audit trail.

## Run the Workflow

The main entry point is the `run_workflow` function in `src/brandguard/workflow.py`. It accepts an audience query and campaign brief, applies governance rules, and returns a structured result.

```python
from brandguard.workflow import run_workflow

result = run_workflow(
    audience_query="Adults age 25–54 in California",
    campaign_brief="Unlimited wireless plan for professionals. $89/month, no contract."
)
```

The function returns a dictionary with these keys:

- **`final_state`**: A dict containing the approved or blocked output. Keys are `audience_filter`, `matched_records`, `generated_copy`, `citations`, `gate_decision`, and `gate_reasons`.
- **`worm_chain`**: A list of immutable event records (write-once read-many log).
- **`worm_chain_verified`**: Boolean indicating whether the WORM chain hash chain is valid.
- **`trace_id`**: A unique identifier for this workflow run.
- **`node_timings_ms`**: A dict mapping node names to execution time in milliseconds.
- **`kill_switch_triggered`**: Boolean; True if the system halted execution due to a safety constraint.

### Check the Gate Decision

After the workflow completes, read the gate decision and copy from the final state:

```python
if result["final_state"] is None:
    print("Workflow halted. Kill switch triggered:", result["kill_switch_triggered"])
else:
    decision = result["final_state"]["gate_decision"]
    copy = result["final_state"]["generated_copy"]
    
    if decision == "ALLOW":
        print("Campaign approved:", copy)
    elif decision == "BLOCK":
        print("Campaign blocked.")
        print("Reasons:", result["final_state"]["gate_reasons"])
```

### Kill Switch Behavior

The system includes a kill switch that halts execution if the `audience_query` parameter is empty. When triggered, `result["kill_switch_triggered"]` is `True` and `result["final_state"]` is `None`. All other fields remain populated for debugging.

## Run the Eval Reports (Q1 Split)

The evaluation harness in `src/brandguard/eval/eval_harness.py` generates two separate reports: one deterministic (committed to version control) and one LLM-based (gitignored).

```bash
python scripts/run_eval_report.py --both
```

This produces:

- `docs/eval_report_deterministic.md`: Committed, verified, reproducible metrics on fixture data.
- `eval_output/eval_report_llm.md`: Gitignored; LLM grading results that vary by model state.

To run only one:

```bash
python scripts/run_eval_report.py --deterministic-only
python scripts/run_eval_report.py --llm-only
```

Each report includes pass rates, failure reasons, and timing statistics. The deterministic report is safe for CI/CD gates; the LLM report is for local development insight.

## Run the Test Suite

Execute all tests from the repository root:

```bash
pytest -q
```

The `pyproject.toml` configuration sets `testpaths = ["tests"]`, so pytest discovers and runs only test files in the `tests/` directory. The `-q` flag suppresses verbose output. Do not point pytest at `src/` directly; the test discovery is configured in the project file.

Tests cover unit cases for the workflow, governance rules, agent behavior, and the WORM logger.

## Run the Doc QC Pipeline

The document quality control system verifies that generated documentation matches a brief, adheres to a rubric, and passes automated checks. Run it with:

```bash
python -m scripts.doc_pipeline.orchestrator --brief BRIEF.brief.md --rubric RUBRIC.rubric.md --output OUT.md
```

Parameters:

- `--brief`: Path to the brief file defining the doc's scope and requirements.
- `--rubric`: Path to the rubric file specifying style, voice, and citation rules.
- `--output`: Path where the verified document will be written.

The orchestrator produces two files:

- `OUT.md`: The final verified document.
- `OUT.md.qc.json`: A sidecar JSON file with QC details, including pass/fail status for each check.

The pipeline runs up to 5 rewrite cycles per DJ-021. Exit code 0 indicates VERIFIED; non-zero exit indicates FAILED. Check the `.qc.json` file for detailed failure reasons.

## Inspect the WORM Chain

Every workflow run produces an immutable event log in the `worm_chain` field. This chain is write-once read-many (WORM), backed by SQLite with append-only triggers and HMAC-SHA256 hash chaining from intelliflow-core.

```python
result = run_workflow(audience_query="...", campaign_brief="...")

print("WORM chain length:", len(result["worm_chain"]))
print("Chain verified:", result["worm_chain_verified"])

for event in result["worm_chain"]:
    print(event["timestamp"], event["node"], event["action"])
```

Each entry contains:

- **`timestamp`**: UTC ISO 8601 timestamp.
- **`node`**: The workflow node that produced the event (e.g., "audience_filter", "llm_copy_gen", "legal_gate").
- **`action`**: A string describing the operation (e.g., "started", "completed", "gating_rule_applied").
- **`hash`**: HMAC-SHA256 digest of this record plus the previous hash (chain verification).
- **`details`**: Structured data specific to the action.

To verify the chain independently, call:

```python
from brandguard.governance.worm import verify_chain

is_valid = verify_chain(result["worm_chain"])
print("Chain integrity:", is_valid)
```

The `verify_chain()` function recomputes the HMAC-SHA256 chain from the first event to the last, confirming no tampering. If any record is modified or deleted, verification fails.

This audit trail is essential for compliance reviews and debugging governance decisions. It is always present, even if `kill_switch_triggered` is True.

# RELY-SE: A Dashboard for Measuring Operational Reliability of AI Coding Agents — Artifact Evaluation Submission

## Paper Title

RELY-SE: A Dashboard for Measuring Operational Reliability of AI Coding Agents

## Purpose

AI coding agents (e.g., Aider, Claude-Code-Pro, AutoCodeRover) are increasingly deployed in production software development, but existing benchmarks such as SWE-bench measure only correctness — whether an agent resolves a given issue. They do not capture operational reliability: whether an agent breaks the CI pipeline, requires human intervention, or behaves inconsistently across repeated runs.

RELY-SE is a framework and interactive Streamlit dashboard that addresses this gap. It ingests structured execution traces from coding agents, computes five reliability metrics adapted from safety-critical domains — Human Intervention Rate (HIR), Commit Failure Rate (CFR), Task Success Rate (TSR), Agent Goal Achievement Reliability (AGAR), and Decision Stability Metric (DSM) — and renders comparative reliability profiles across agents and tasks through three interactive views (Comparative Overview, Agent Deep-Dive, Failure Analysis).

This artifact provides the complete RELY-SE source code, the trace ingestion and metric computation pipeline, 135 bundled execution traces from the paper's demonstration (3 agents × 15 SWE-bench Lite tasks × 3 trials), and documentation sufficient to install, run, and extend the tool.

## Badge(s) Requested

- Artifacts Available
- Artifacts Functional 
- Artifacts Reusable

**Justification:** The artifact is publicly archived on Zenodo with a persistent DOI (10.5281/zenodo.21174225) and hosted on a public GitHub repository under the MIT License, satisfying the Available badge. It further meets the Reusable badge criteria through its modular, independently extensible architecture (adding a new agent requires implementing a single parsing function; adding a new metric requires a single function addition), thorough documentation including a sub-5-minute smoke test requiring no API credentials, and bundled sample data enabling full exploration of the tool without live agent execution. Full justification is provided in the artifact's `STATUS` file.

## Technology Skills Assumed / Hardware Requirements

Reviewers should be comfortable with:

- Basic command-line usage (cloning a repository, running Python scripts)
- Python package management via pip

No specialized hardware, GPU, Docker, or VM is required. The artifact runs on any standard machine with:

- Python 3.11+
- 8 GB RAM (minimum)
- ~500 MB free disk space
- Ubuntu 22.04+ or macOS 13+ (Windows via WSL2 expected to work, untested)

An internet connection is required only to download SWE-bench task metadata (`select_tasks.py`) or to run live agent evaluation via the Anthropic API (`run_aider.py`). Neither is required for the smoke test, which runs entirely offline using bundled sample data. Full details are in the artifact's `REQUIREMENTS` file.

## Provenance

The artifact is permanently archived on Zenodo:

- **DOI:** 10.5281/zenodo.21174225
- https://doi.org/10.5281/zenodo.21174225

The archive was created via the GitHub–Zenodo integration from the public source repository:

- https://github.com/Akileshdash/Rely-SE.git

A demonstration video is also available:

- https://youtu.be/RjYReUyznqI

## Instructions

1. Access the artifact via the Zenodo DOI above, or clone the GitHub repository directly:

   ```bash
   git clone https://github.com/rishalab/Rely-SE.git
   cd Rely-SE
   ```

2. Install dependencies (Python 3.11+ required):

   ```bash
   pip install -r requirements.txt
   ```

3. Run the smoke test (< 5 minutes, no API key needed):

   ```bash
   python generate_sample_traces.py
   streamlit run dashboard.py
   ```

   This generates sample execution traces, computes `metrics_aggregated.csv`, and launches the dashboard at `http://localhost:8501` with all three tabs populated.

4. To reproduce the paper's Table 2 results (3 agents, 15 SWE-bench Lite tasks, 3 trials = 135 runs), follow the "Reproducing the Paper Results" section of `README.md`. This uses the exact task list bundled in `data/benchmark_tasks.csv` and, for Aider, supports live re-execution given an Anthropic API key (optional — the 135 traces from the original run are already included in the repository/archive).

5. Full setup, smoke test, and reproduction instructions are in `README.md` at the repository root. Architecture and dependency details are in `REQUIREMENTS`. Badge justification is in `STATUS`.

No specific operating system beyond the above, no GPUs, and no reviewer-provided credentials are required to complete the Getting Started guide within 30 minutes.

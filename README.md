# RELY-SE: A Dashboard for Measuring Operational Reliability of AI Coding Agents

RELY-SE is a framework and interactive dashboard for evaluating the **operational reliability** of AI coding agents beyond correctness. It implements five reliability metrics — HIR, CFR, TSR, AGAR, and DSM — adapted from safety-critical domains (SRE, autonomous vehicles, aviation, medical AI), and renders them through an interactive Streamlit dashboard.

This artifact accompanies the ASE 2026 Tools and Datasets paper:

> Akilesh P, Shivadharshan S, Sridhar Chimalakonda, Vibhu Saujanya Sharma, and Vikrant Kaulgud. 2026. **RELY-SE: A Dashboard for Measuring Operational Reliability of AI Coding Agents**. In *Proceedings of the 41st IEEE/ACM International Conference on Automated Software Engineering (ASE '26)*. ACM, New York, NY, USA, 4 pages.

Repository: https://github.com/rishalab/Rely-SE.git
Demo video: https://youtu.be/RjYReUyznqI
Archived artifact (Zenodo DOI): https://doi.org/10.5281/zenodo.21172260

---

## Table of Contents

- Overview
- Requirements
- Installation
- Quick Start
- Smoke Test
- Reproducing the Paper Results
- Reliability Metrics
- Project Workflow
- Trace Format
- Project Structure
- Supported Paper Claims
- License
- Citation

---

## Overview

RELY-SE evaluates AI coding agents using five complementary operational reliability metrics:

| Metric | Measures | Better |
|--------|----------|--------|
| **HIR** | Human Intervention Rate | Lower |
| **CFR** | Commit Failure Rate (CI/CD stability) | Lower |
| **TSR** | Task Success Rate (correctness, no regressions) | Higher |
| **AGAR** | Agent Goal Achievement Reliability (success rate among completed runs) | Higher |
| **DSM** | Decision Stability Metric (consistency across trials) | Higher [0.5–1.0] |

**Key insight from the paper:** agents with near-identical TSR can have very different CFR. In our evaluation, AutoCodeRover and Aider both score 13.3% TSR, but AutoCodeRover's CFR (12.2%) is higher than Aider's (10.0%) — a difference invisible to correctness-only benchmarks like SWE-bench.

---

## Requirements

Tested on:

- Ubuntu 22.04 LTS / macOS 13+
- Python 3.11+
- 8 GB RAM (minimum)
- Internet connection (only required for `select_tasks.py`, which downloads SWE-bench task metadata)
- Anthropic API key (only required to run Aider against Claude models, or to reproduce live agent runs — **not required for the smoke test or demo mode**)

See the `REQUIREMENTS` file for the machine-readable dependency list (`requirements.txt`) and architecture notes.

---

## Installation

```bash
git clone https://github.com/rishalab/Rely-SE.git
cd Rely-SE
pip install -r requirements.txt
```

---

## Quick Start

### Option A — Demo with sample data (no API key, no agents needed)

```bash
python generate_sample_traces.py
streamlit run dashboard.py
```

`generate_sample_traces.py` both generates execution traces **and** computes `data/metrics_aggregated.csv` in one step — you do not need to run `compute_metrics.py` separately in this path.

> **Note on demo data:** by default this generates traces for five illustrative agent profiles (SWE-Agent, AutoCodeRover, Aider, Claude-Code, OpenHands) using generic task IDs, to showcase the dashboard's full feature set without requiring `select_tasks.py`. This is broader than the 3-agent, 15-task evaluation reported in the paper — see **Reproducing the Paper Results** below for the exact configuration used in Table 2.

### Option B — Reproduce experiments using Aider on real SWE-bench tasks

```bash
python select_tasks.py
export ANTHROPIC_API_KEY=<your_key>
python run_aider.py --trials 1
streamlit run dashboard.py
```

---

## Smoke Test

To verify the artifact is installed and working (should take under 5 minutes, no API key required):

```bash
python generate_sample_traces.py
streamlit run dashboard.py
```

Expected outcome:

- Console output confirms sample traces were generated (225 files across 5 agents) and `data/metrics_aggregated.csv` was written.
- The Streamlit dashboard opens at `http://localhost:8501`.
- Three tabs are visible: **Comparative Overview**, **Agent Deep-Dive**, **Failure Analysis**.
- All five reliability metrics (HIR, CFR, TSR, AGAR, DSM) are displayed and selectable.

---

## Reproducing the Paper Results

Table 2 in the paper reports metrics for **3 agents** (Aider, Claude-Code-Pro, AutoCodeRover) on **15 SWE-bench Lite tasks** (10 Django, 5 Matplotlib) × 3 trials = 135 runs.

To reproduce this exact configuration:

```bash
python select_tasks.py --tasks django__django-11179 django__django-11999 \
  django__django-12470 django__django-12983 django__django-13230 \
  django__django-10914 django__django-10924 django__django-11001 \
  django__django-11039 django__django-11049 \
  matplotlib__matplotlib-18869 matplotlib__matplotlib-22711 \
  matplotlib__matplotlib-22835 matplotlib__matplotlib-23299 \
  matplotlib__matplotlib-23314
python run_aider.py --trials 3
python compute_metrics.py
streamlit run dashboard.py
```

> **Please verify this `select_tasks.py` flag/argument name matches your actual CLI before submission** — if the script doesn't currently support pinning an explicit task list, add that option or ship a pre-built `data/benchmark_tasks.csv` with these exact 15 task IDs so reviewers don't have to guess.

As reported in the paper, Claude-Code-Pro and AutoCodeRover profiles in this demonstration are populated from published SWE-bench Lite leaderboard TSR values combined with operationally representative CFR/HIR parameters, rather than from live execution; Aider traces reflect direct runs. Absolute metric values should be interpreted as illustrative of the tool's analytical capability rather than as definitive agent rankings — this caveat is stated explicitly in the paper (Section 5.1) and applies to this artifact.

Approximate runtime for live Aider runs: varies with API latency; budget 1–2 hours for 15 tasks × 3 trials.

---

## Reliability Metrics

| Metric | Formula | Adapted from |
|--------|---------|---------------|
| HIR | # interventions / N | AV disengagement rates |
| CFR | # broken commits / M | SRE Site Reliability Engineering |
| TSR | # correct, no regression / N | SWE-bench "resolved" rate |
| AGAR | # successes / # completions | Aviation MTBF |
| DSM | max(k/n, (n−k)/n) | Stochastic stability |

*N = total runs; M = commits proposed; k = successes; n = trials.*

Full definitions are in `docs/METRIC_DEFINITIONS.md` and Section 4 of the paper.

---

## Project Workflow

```
select_tasks.py          → data/benchmark_tasks.csv
run_aider.py              → data/traces/aider/*.json
generate_sample_traces.py → data/traces/<agent>/*.json + data/metrics_aggregated.csv (demo mode, all-in-one)
compute_metrics.py        → data/metrics_aggregated.csv (use after run_aider.py)
streamlit run dashboard.py → interactive dashboard
```

---

## Trace Format

Each execution produces one JSON trace with ten fields:

```json
{
  "agent": "Aider",
  "task_id": "django__django-11049",
  "trial": 1,
  "success": true,
  "intervention_required": false,
  "commit_proposed": true,
  "build_broken": false,
  "regression": false,
  "completed": true,
  "duration_seconds": 142.3,
  "error_message": ""
}
```

See `examples/trace_format.json` and `docs/METRIC_DEFINITIONS.md`. New agents can be supported by implementing a single parsing function in `trace_processor.py`.

---

## Project Structure

```
rely-se/
├── dashboard.py               # Streamlit app (3 tabs)
├── metric_engine.py           # HIR/CFR/TSR/AGAR/DSM computation
├── trace_processor.py         # Parse agent logs → trace JSON
├── select_tasks.py            # Download & select SWE-bench tasks
├── run_aider.py                # Run Aider on benchmark tasks
├── generate_sample_traces.py  # Generate demo traces + metrics
├── compute_metrics.py         # Aggregate traces → metrics CSV
├── requirements.txt
├── data/
│   ├── traces/                # One subfolder per agent
│   ├── metrics_aggregated.csv
│   └── benchmark_tasks.csv
├── examples/
├── docs/
├── tests/
├── README.md
├── REQUIREMENTS
├── STATUS
└── LICENSE
```

---

## Supported Paper Claims

This artifact supports:

- ✓ Computation of all five reliability metrics (HIR, CFR, TSR, AGAR, DSM) — `metric_engine.py`
- ✓ The trace schema and ingestion pipeline described in Section 3.2 — `trace_processor.py`
- ✓ The three-tab dashboard (Comparative Overview, Agent Deep-Dive, Failure Analysis) described in Section 3.4
- ✓ Table 2's aggregated metrics, when run with the exact 15-task configuration and Aider live execution described above
- ✓ Findings 1–4 (Section 5.2), reproducible from the same data

Not supported / requires reviewer resources:

- Live Claude-Code-Pro and AutoCodeRover execution — the repository currently ships a live-run script only for Aider; Claude-Code-Pro and AutoCodeRover figures in the paper come from published leaderboard values plus representative parameters, not from a bundled runner script. Full live re-execution of all three agents requires the reviewer's own commercial API access to each system.
- The full 300-task SWE-bench Lite evaluation mentioned as future work (Section 7) — only the 15-task subset is included.

---

## License

This project is released under the MIT License. See `LICENSE`.

---

## Citation

```bibtex
@inproceedings{relyse2026,
  author    = {Akilesh P and Shivadharshan S and Sridhar Chimalakonda and Vibhu Saujanya Sharma and Vikrant Kaulgud},
  title     = {RELY-SE: A Dashboard for Measuring Operational Reliability of AI Coding Agents},
  booktitle = {Proceedings of the 41st IEEE/ACM International Conference on Automated Software Engineering (ASE '26)},
  year      = {2026},
  publisher = {ACM},
  address   = {New York, NY, USA}
}
```

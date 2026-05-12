# RELY-SE: AI Coding Agent Reliability Dashboard

Operational reliability evaluation of AI coding agents beyond correctness.

---

## Quick Start

```bash
pip install -r requirements.txt

# Option A: Run with sample data immediately (no agents needed)
python generate_sample_traces.py
streamlit run dashboard.py

# Option B: Select real SWE-bench tasks and run Aider
python select_tasks.py
export ANTHROPIC_API_KEY=your_key
python run_aider.py --trials 1        # smoke test (1 trial per task)
python compute_metrics.py
streamlit run dashboard.py
```

---

## The Five Metrics

| Metric | Measures | Better |
|--------|----------|--------|
| **HIR** | Human Intervention Rate | Lower |
| **CFR** | Commit Failure Rate (CI stability) | Lower |
| **TSR** | Task Success Rate (correctness) | Higher |
| **AGAR** | Goal Achievement Reliability | Higher |
| **DSM** | Decision Stability (0.5–1.0) | Higher |

**Key insight:** Agents with similar TSR can have very different CFR.
An agent passing 72% of tasks but breaking CI 31% of the time is
unsuitable for production despite strong correctness numbers.

---

## Workflow

```
select_tasks.py          → data/benchmark_tasks.csv
run_aider.py             → data/traces/aider/*.json
compute_metrics.py       → data/metrics_aggregated.csv
streamlit run dashboard.py
```

---

## Trace Format

Each agent run produces one JSON file:

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

See `examples/trace_format.json` and `docs/METRIC_DEFINITIONS.md`.

---

## Project Structure

```
rely-se/
├── dashboard.py              # Streamlit app
├── metric_engine.py          # HIR/CFR/TSR/AGAR/DSM computation
├── trace_processor.py        # Parse agent logs → trace JSON
├── select_tasks.py           # Download & select SWE-bench tasks
├── run_aider.py              # Run Aider on benchmark tasks
├── generate_sample_traces.py # Generate sample data for demo
├── compute_metrics.py        # Aggregate traces → metrics CSV
├── data/
│   ├── traces/               # One subfolder per agent
│   ├── metrics_aggregated.csv
│   └── benchmark_tasks.csv
├── examples/
├── tests/
└── docs/
```

---

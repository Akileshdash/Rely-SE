"""
examples/usage_example.py
==========================
Shows how to load traces and compute metrics programmatically.
Run from the rely-se/ root:
    python examples/usage_example.py
"""

import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from metric_engine import MetricEngine, ExecutionTrace

# ── Option A: Load from JSON files ───────────────────────────────────────────
engine = MetricEngine()
traces_dir = Path("data/traces")

if traces_dir.exists():
    # Manually recurse (load_traces_from_json only reads flat dirs)
    for f in traces_dir.rglob("*.json"):
        try:
            with open(f) as fp:
                engine.traces.append(ExecutionTrace(**json.load(fp)))
        except Exception:
            pass
    print(f"Loaded {len(engine.traces)} traces\n")

# ── Option B: Build traces in code ───────────────────────────────────────────
if not engine.traces:
    print("No trace files found — using inline example data\n")
    engine.traces = [
        ExecutionTrace("Aider","django__django-11049",1,True,False,True,False,False,True,88.0),
        ExecutionTrace("Aider","django__django-11049",2,True,False,True,False,False,True,92.0),
        ExecutionTrace("Aider","django__django-11049",3,False,False,True,True, False,True,75.0),
        ExecutionTrace("Claude-Code","django__django-11049",1,True,False,True,False,False,True,55.0),
        ExecutionTrace("Claude-Code","django__django-11049",2,True,False,True,False,False,True,48.0),
        ExecutionTrace("Claude-Code","django__django-11049",3,True,False,True,False,False,True,61.0),
    ]

# ── Compute per-agent metrics ─────────────────────────────────────────────────
print("=== Per-Agent Metrics ===")
for agent in sorted(set(t.agent for t in engine.traces)):
    subset = [t for t in engine.traces if t.agent == agent]
    m = engine.compute_all_metrics(subset)
    print(f"\n{agent}:")
    for k, v in m.items():
        print(f"  {k}: {v:.3f}")

# ── Key insight: TSR vs CFR ───────────────────────────────────────────────────
print("\n=== TSR vs CFR (the reliability gap) ===")
agents = sorted(set(t.agent for t in engine.traces))
for agent in agents:
    subset = [t for t in engine.traces if t.agent == agent]
    m = engine.compute_all_metrics(subset)
    print(f"  {agent:20s}  TSR={m['TSR']:.2f}  CFR={m['CFR']:.2f}")

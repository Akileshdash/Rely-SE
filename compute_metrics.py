"""
compute_metrics.py
==================
Reads all traces from data/traces/ and writes data/metrics_aggregated.csv.
Run this after every agent run to refresh the dashboard.

Run:
    python compute_metrics.py
"""

import sys
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from metric_engine import MetricEngine


def compute_metrics(traces_dir: str = "data/traces",
                    out_csv: str = "data/metrics_aggregated.csv"):
    engine = MetricEngine()

    traces_path = Path(traces_dir)
    if not traces_path.exists():
        print(f"ERROR: {traces_path} does not exist. Run an agent first.")
        sys.exit(1)

    # metric_engine.load_traces_from_json only reads one flat directory.
    # We need to recurse into subfolders (one per agent).
    import json
    from metric_engine import ExecutionTrace

    all_json = list(traces_path.rglob("*.json"))
    if not all_json:
        print(f"No JSON trace files found under {traces_path}")
        sys.exit(1)

    loaded = 0
    for f in all_json:
        try:
            with open(f) as fp:
                d = json.load(fp)
            engine.traces.append(ExecutionTrace(**d))
            loaded += 1
        except Exception as e:
            print(f"  WARNING: skipping {f.name}: {e}")

    print(f"Loaded {loaded} traces from {traces_path}")

    agents = sorted(set(t.agent for t in engine.traces))
    tasks  = sorted(set(t.task_id for t in engine.traces))
    print(f"Agents : {agents}")
    print(f"Tasks  : {len(tasks)}")

    rows = []
    for agent in agents:
        for task in tasks:
            subset = [t for t in engine.traces
                      if t.agent == agent and t.task_id == task]
            if not subset:
                continue
            m = engine.compute_all_metrics(subset)

            # Per-task std across trials
            import numpy as np
            trial_successes = [t.success for t in subset]
            rows.append({
                "agent":     agent,
                "task":      task,
                "HIR_mean":  round(m["HIR"],  3),
                "CFR_mean":  round(m["CFR"],  3),
                "TSR_mean":  round(m["TSR"],  3),
                "AGAR_mean": round(m["AGAR"], 3),
                "DSM_mean":  round(m["DSM"],  3),
                "HIR_std":   0.0,
                "CFR_std":   0.0,
                "TSR_std":   round(float(np.std([t.success for t in subset])), 3),
                "AGAR_std":  0.0,
                "DSM_std":   0.0,
                "n_trials":  len(subset),
            })

    df = pd.DataFrame(rows)
    Path(out_csv).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_csv, index=False)
    print(f"\n✅ Saved {len(df)} rows to {out_csv}")

    print("\nPer-agent summary:")
    summary = df.groupby("agent")[
        ["HIR_mean", "CFR_mean", "TSR_mean", "AGAR_mean", "DSM_mean"]
    ].mean().round(3)
    print(summary.to_string())
    return df


if __name__ == "__main__":
    compute_metrics()

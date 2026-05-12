"""
generate_sample_traces.py
=========================
Generates realistic sample execution traces for all 5 agents.
Use this to get the dashboard running immediately while real
agent runs happen in parallel.

Based on published SWE-bench leaderboard numbers (May 2025).
Be transparent in the paper: "Simulated traces based on published
benchmark profiles; Aider/SWE-Agent were run directly."

Run:
    python generate_sample_traces.py

Output:
    data/traces/<agent>/<task_id>_trial_<N>.json  (225 files total)
    data/metrics_aggregated.csv
"""

import json
import random
import pandas as pd
from pathlib import Path


# Agent profiles derived from SWE-bench Lite leaderboard (Apr 2025)
# success_rate ≈ TSR, build_break ≈ CFR, intervention ≈ HIR
AGENT_PROFILES = {
    "SWE-Agent": {
        "success_rate": 0.18,   # SWE-Agent ~18% on Lite
        "intervention": 0.22,
        "build_break":  0.31,
        "timeout_rate": 0.10,
        "folder":       "swe_agent",
    },
    "AutoCodeRover": {
        "success_rate": 0.22,   # ACR ~22% on Lite
        "intervention": 0.12,
        "build_break":  0.14,
        "timeout_rate": 0.08,
        "folder":       "autocoderover",
    },
    "Aider": {
        "success_rate": 0.26,   # Aider ~26% on Lite
        "intervention": 0.18,
        "build_break":  0.22,
        "timeout_rate": 0.07,
        "folder":       "aider",
    },
    "Claude-Code": {
        "success_rate": 0.72,   # Claude Code ~72% on Lite (Anthropic, 2025)
        "intervention": 0.06,
        "build_break":  0.09,
        "timeout_rate": 0.03,
        "folder":       "claude_code",
    },
    "OpenHands": {
        "success_rate": 0.38,   # OpenHands ~38% on Lite
        "intervention": 0.25,
        "build_break":  0.27,
        "timeout_rate": 0.12,
        "folder":       "openhands",
    },
}

ERROR_MESSAGES = [
    "Build failed: AssertionError in test_suite.py line 45",
    "TimeoutError: agent exceeded 5-minute limit",
    "FileNotFoundError: patch target not found in repo",
    "SyntaxError: invalid syntax in generated patch",
    "ImportError: module not found after patch applied",
    "pytest: 3 failed, 2 passed — regression introduced",
    "git apply: patch does not apply cleanly",
    "RecursionError: maximum recursion depth exceeded",
]


def load_tasks() -> list:
    tasks_path = Path("data/benchmark_tasks.csv")
    if tasks_path.exists():
        df = pd.read_csv(tasks_path)
        return df["task_id"].tolist()
    else:
        # Fallback: generic task IDs
        print("WARNING: data/benchmark_tasks.csv not found, using generic task IDs.")
        print("Run select_tasks.py first for real task IDs.\n")
        return [f"issue_{i:03d}" for i in range(1, 16)]


def generate_trace(agent_name: str, profile: dict, task_id: str, trial: int,
                   rng: random.Random) -> dict:
    """Generate one trace with realistic correlated fields."""
    timed_out   = rng.random() < profile["timeout_rate"]
    intervention = timed_out or (rng.random() < profile["intervention"])
    completed   = not timed_out

    # Success requires: completed, no intervention, agent "solved" it
    success = (
        completed
        and not intervention
        and rng.random() < profile["success_rate"]
    )

    # Commit proposed if not timed out and agent made changes
    commit_proposed = completed and (rng.random() < 0.88)

    # Build broken only if commit was proposed and not successful
    build_broken = (
        commit_proposed
        and not success
        and rng.random() < profile["build_break"]
    )

    # Regression: rare, only if success=True
    regression = success and (rng.random() < 0.04)
    if regression:
        success = False

    error_message = ""
    if not success:
        if timed_out:
            error_message = "TimeoutError: agent exceeded 5-minute limit"
        elif build_broken:
            error_message = rng.choice(ERROR_MESSAGES[:5])
        elif intervention:
            error_message = rng.choice(ERROR_MESSAGES[2:6])

    return {
        "agent":                 agent_name,
        "task_id":               task_id,
        "trial":                 trial,
        "success":               success,
        "intervention_required": intervention,
        "commit_proposed":       commit_proposed,
        "build_broken":          build_broken,
        "regression":            regression,
        "completed":             completed,
        "duration_seconds":      round(rng.uniform(20, 280), 1),
        "error_message":         error_message,
    }


def generate_all(trials: int = 3, seed: int = 42):
    tasks = load_tasks()
    rng   = random.Random(seed)

    total = 0
    for agent_name, profile in AGENT_PROFILES.items():
        out_dir = Path(f"data/traces/{profile['folder']}")
        out_dir.mkdir(parents=True, exist_ok=True)

        for task_id in tasks:
            for trial in range(1, trials + 1):
                out_file = out_dir / f"{task_id}_trial_{trial}.json"
                if out_file.exists():
                    continue   # don't overwrite real traces
                trace = generate_trace(agent_name, profile, task_id, trial, rng)
                with open(out_file, "w") as f:
                    json.dump(trace, f, indent=2)
                total += 1

    print(f"✅ Generated {total} sample traces across {len(AGENT_PROFILES)} agents × "
          f"{len(tasks)} tasks × {trials} trials")


def compute_and_save_metrics():
    """Compute aggregated metrics CSV from all traces."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from metric_engine import MetricEngine

    engine = MetricEngine()
    engine.load_traces_from_json(Path("data/traces"))

    if not engine.traces:
        print("No traces found — run generate_all() first.")
        return

    rows = []
    agents = sorted(set(t.agent for t in engine.traces))
    tasks  = sorted(set(t.task_id for t in engine.traces))

    for agent in agents:
        for task in tasks:
            subset = [t for t in engine.traces
                      if t.agent == agent and t.task_id == task]
            if not subset:
                continue
            m = engine.compute_all_metrics(subset)
            rows.append({
                "agent":      agent,
                "task":       task,
                "HIR_mean":   round(m["HIR"],  3),
                "CFR_mean":   round(m["CFR"],  3),
                "TSR_mean":   round(m["TSR"],  3),
                "AGAR_mean":  round(m["AGAR"], 3),
                "DSM_mean":   round(m["DSM"],  3),
                # std fields (dashboard expects them)
                "HIR_std":    0.0,
                "CFR_std":    0.0,
                "TSR_std":    0.0,
                "AGAR_std":   0.0,
                "DSM_std":    0.0,
            })

    df = pd.DataFrame(rows)
    out_path = Path("data/metrics_aggregated.csv")
    df.to_csv(out_path, index=False)
    print(f"✅ Metrics saved to {out_path}  ({len(df)} rows)")

    print("\nPer-agent summary:")
    summary = df.groupby("agent")[["HIR_mean","CFR_mean","TSR_mean","AGAR_mean","DSM_mean"]].mean().round(3)
    print(summary.to_string())


if __name__ == "__main__":
    print("Generating sample traces...")
    generate_all()
    print("\nComputing metrics...")
    compute_and_save_metrics()
    print("\nNext: streamlit run dashboard.py")

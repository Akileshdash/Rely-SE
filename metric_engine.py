"""
RELY-SE Metric Engine
=====================
Compute operational reliability metrics for AI coding agents.

Metrics:
- HIR (Human Intervention Rate): Fraction of tasks requiring human takeover
- CFR (Commit Failure Rate): % of commits that break builds/tests
- TSR (Task Success Rate): % of tasks resolved correctly
- AGAR (Agent Goal Achievement Reliability): Prob. of success under constraints
- DSM (Decision Stability Metric): Consistency across repeated runs (0.5–1.0)
"""

import json
import numpy as np
from typing import Dict, List, Tuple
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ExecutionTrace:
    """Represents a single agent-task-trial execution."""
    agent: str
    task_id: str
    trial: int
    success: bool
    intervention_required: bool
    commit_proposed: bool
    build_broken: bool
    regression: bool
    completed: bool
    duration_seconds: float = 0.0
    error_message: str = ""


class MetricEngine:
    """Computes RELY-SE metrics from agent execution traces."""
    
    def __init__(self):
        self.traces: List[ExecutionTrace] = []
    
    def load_traces_from_json(self, traces_dir: Path) -> None:
        """
        Load execution traces from JSON files.
        Expected format per file:
        {
            "agent": "SWE-Agent",
            "task_id": "django-12345",
            "trial": 1,
            "success": True,
            "intervention_required": False,
            "commit_proposed": True,
            "build_broken": False,
            "regression": False,
            "completed": True,
            "duration_seconds": 120.5,
            "error_message": ""
        }
        """
        self.traces = []
        for trace_file in traces_dir.glob("*.json"):
            try:
                with open(trace_file) as f:
                    data = json.load(f)
                    self.traces.append(ExecutionTrace(**data))
            except Exception as e:
                print(f"Warning: Failed to load {trace_file}: {e}")
    
    def compute_HIR(self, traces: List[ExecutionTrace]) -> float:
        """
        Human Intervention Rate (HIR)
        
        Definition: Fraction of tasks requiring human takeover due to 
                   unrecoverable errors or unsafe operations.
        
        Formula: HIR = (# tasks with intervention) / N
        
        Range: [0.0, 1.0]
        - 0.0: Never requires intervention (autonomous)
        - 1.0: Always requires intervention (not autonomous)
        """
        if not traces:
            return 0.0
        
        interventions = sum(1 for t in traces if t.intervention_required)
        hir = interventions / len(traces)
        return hir
    
    def compute_CFR(self, traces: List[ExecutionTrace]) -> float:
        """
        Commit Failure Rate (CFR)
        
        Definition: Percentage of agent-proposed commits that break builds 
                   or cause test failures.
        
        Formula: CFR = (# patches breaking builds/tests) / M
                 where M = # patches proposed
        
        Range: [0.0, 1.0]
        - 0.0: All commits pass CI
        - 1.0: All commits break CI (or none proposed → undefined → 0.0)
        
        Adapted from: Site Reliability Engineering (SRE) change failure rate
        """
        commits_proposed = sum(1 for t in traces if t.commit_proposed)
        
        if commits_proposed == 0:
            return 0.0  # No commits proposed
        
        broken_commits = sum(
            1 for t in traces 
            if t.commit_proposed and t.build_broken
        )
        cfr = broken_commits / commits_proposed
        return cfr
    
    def compute_TSR(self, traces: List[ExecutionTrace]) -> float:
        """
        Task Success Rate (TSR)
        
        Definition: Percentage of bug-fixing tasks correctly resolved 
                   without introducing regressions.
        
        Formula: TSR = (# tasks resolved correctly) / N
                 where a task is resolved iff:
                 - All originally failing tests pass
                 - No new test failures (no regression)
                 - Root cause addressed
        
        Range: [0.0, 1.0]
        - 0.0: No tasks succeeded
        - 1.0: All tasks succeeded
        
        Adapted from: Medical AI treatment success metrics
        """
        if not traces:
            return 0.0
        
        successes = sum(
            1 for t in traces 
            if t.success and not t.regression
        )
        tsr = successes / len(traces)
        return tsr
    
    def compute_AGAR(self, traces: List[ExecutionTrace]) -> float:
        """
        Agent Goal Achievement Reliability (AGAR)
        
        Definition: Probability that the agent successfully achieves its 
                   assigned goal under specified resource constraints 
                   (timeouts, retries, memory limits).
        
        Formula: AGAR = (# successful completions) / (# completions)
                 where:
                 - Completion = finished within time/resource limits
                 - Success = completed AND achieved goal
        
        Range: [0.0, 1.0]
        - 0.0: No goals achieved (or no completions)
        - 1.0: All completions succeeded
        
        Differs from TSR: AGAR accounts for timeouts/resource exhaustion
        TSR measures correctness conditional on completing.
        
        Adapted from: Aviation MTBF and goal-achievement reliability
        """
        completed = sum(1 for t in traces if t.completed)
        
        if completed == 0:
            return 0.0  # No completions (all timed out/ran out of resources)
        
        successful_completions = sum(
            1 for t in traces 
            if t.completed and t.success
        )
        agar = successful_completions / completed
        return agar
    
    def compute_DSM(self, trial_outcomes: List[bool]) -> float:
        """
        Decision Stability Metric (DSM)
        
        Definition: Consistency of agent decisions across repeated runs 
                   under identical inputs. Measures predictability of 
                   stochastic agent behavior.
        
        Formula: DSM = max(k/n, (n-k)/n)
                 where:
                 - n = # independent trials
                 - k = # successes
                 - Outcome ∈ {success, failure}
        
        Range: [0.5, 1.0]
        - 0.5: Maximal inconsistency (coin flip: 50% success, 50% failure)
        - 0.6–0.8: High variability (unpredictable)
        - 0.8–1.0: Stable (deterministic or highly consistent)
        - 1.0: Perfect consistency (always succeed or always fail)
        
        Interpretation:
        - High DSM (>0.9): Behavior is predictable; easy to plan around
        - Low DSM (<0.7): Behavior is stochastic; requires monitoring
        
        Adapted from: Stochastic process stability literature
        """
        if not trial_outcomes:
            return 0.5  # Undefined → neutral
        
        n = len(trial_outcomes)
        k = sum(trial_outcomes)  # Count successes (True = 1)
        
        dsm = max(k / n, (n - k) / n)
        return dsm
    
    def compute_all_metrics(
        self, 
        traces: List[ExecutionTrace]
    ) -> Dict[str, float]:
        """
        Compute all 5 RELY-SE Tier-1 metrics.
        
        Args:
            traces: List of ExecutionTrace objects (typically for one agent-task pair)
        
        Returns:
            {
                'HIR': float,    # Human Intervention Rate
                'CFR': float,    # Commit Failure Rate
                'TSR': float,    # Task Success Rate
                'AGAR': float,   # Agent Goal Achievement Reliability
                'DSM': float     # Decision Stability Metric
            }
        """
        # Separate trial outcomes for DSM
        trial_outcomes = [t.success for t in traces]
        
        metrics = {
            'HIR': self.compute_HIR(traces),
            'CFR': self.compute_CFR(traces),
            'TSR': self.compute_TSR(traces),
            'AGAR': self.compute_AGAR(traces),
            'DSM': self.compute_DSM(trial_outcomes)
        }
        return metrics
    
    def aggregate_by_agent(self) -> Dict[str, Dict[str, float]]:
        """
        Aggregate metrics by agent (mean across all tasks).
        
        Returns:
            {
                'SWE-Agent': {
                    'HIR_mean': 0.15,
                    'HIR_std': 0.08,
                    'CFR_mean': 0.12,
                    ...
                },
                'AutoCodeRover': {...},
                ...
            }
        """
        agents = set(t.agent for t in self.traces)
        results = {}
        
        for agent in agents:
            agent_traces = [t for t in self.traces if t.agent == agent]
            metrics = self.compute_all_metrics(agent_traces)
            
            results[agent] = {
                f"{k}_mean": v 
                for k, v in metrics.items()
            }
            
            # Compute std dev if multiple trials per agent
            if len(agent_traces) > 1:
                for metric in ['HIR', 'CFR', 'TSR', 'AGAR']:
                    # Group by task, compute metric for each, then std
                    tasks = set(t.task_id for t in agent_traces)
                    task_metrics = []
                    for task in tasks:
                        task_traces = [t for t in agent_traces if t.task_id == task]
                        task_metric = self.compute_all_metrics(task_traces)[metric]
                        task_metrics.append(task_metric)
                    
                    if task_metrics:
                        results[agent][f"{metric}_std"] = float(np.std(task_metrics))
                
                # DSM std (already trial-based)
                dsm_values = [
                    self.compute_DSM([t.success for t in group])
                    for agent_name, group in [
                        (a, [t for t in agent_traces if t.task_id == task_id])
                        for task_id in set(t.task_id for t in agent_traces)
                    ]
                ]
                if dsm_values:
                    results[agent]['DSM_std'] = float(np.std(dsm_values))
        
        return results
    
    def to_dataframe(self):
        """
        Export aggregated metrics as a pandas DataFrame.
        Requires: pip install pandas
        """
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("pandas required. Install: pip install pandas")
        
        agg = self.aggregate_by_agent()
        df = pd.DataFrame(agg).T
        return df


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    # Example: Create traces and compute metrics
    
    traces = [
        # SWE-Agent on issue-123: 3 trials
        ExecutionTrace(
            agent="SWE-Agent", task_id="issue-123", trial=1,
            success=True, intervention_required=False,
            commit_proposed=True, build_broken=False,
            regression=False, completed=True
        ),
        ExecutionTrace(
            agent="SWE-Agent", task_id="issue-123", trial=2,
            success=True, intervention_required=False,
            commit_proposed=True, build_broken=False,
            regression=False, completed=True
        ),
        ExecutionTrace(
            agent="SWE-Agent", task_id="issue-123", trial=3,
            success=False, intervention_required=True,
            commit_proposed=True, build_broken=True,
            regression=False, completed=True
        ),
        
        # AutoCodeRover on issue-123: 3 trials
        ExecutionTrace(
            agent="AutoCodeRover", task_id="issue-123", trial=1,
            success=True, intervention_required=False,
            commit_proposed=True, build_broken=False,
            regression=False, completed=True
        ),
        ExecutionTrace(
            agent="AutoCodeRover", task_id="issue-123", trial=2,
            success=True, intervention_required=False,
            commit_proposed=True, build_broken=False,
            regression=False, completed=True
        ),
        ExecutionTrace(
            agent="AutoCodeRover", task_id="issue-123", trial=3,
            success=True, intervention_required=False,
            commit_proposed=True, build_broken=False,
            regression=False, completed=True
        ),
    ]
    
    # Compute metrics
    engine = MetricEngine()
    engine.traces = traces
    
    print("=== Metrics by Agent ===")
    agg = engine.aggregate_by_agent()
    for agent, metrics in agg.items():
        print(f"\n{agent}:")
        for metric, value in metrics.items():
            if isinstance(value, float):
                print(f"  {metric}: {value:.3f}")
    
    print("\n=== Sample Traces ===")
    swe_metrics = engine.compute_all_metrics([t for t in traces if t.agent == "SWE-Agent"])
    print(f"SWE-Agent metrics: {swe_metrics}")
    
    auto_metrics = engine.compute_all_metrics([t for t in traces if t.agent == "AutoCodeRover"])
    print(f"AutoCodeRover metrics: {auto_metrics}")

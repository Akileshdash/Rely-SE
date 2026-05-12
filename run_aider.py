"""
run_aider.py (IMPROVED - Better Prompts)
=========================================
Improved version with better prompts to get Aider to actually make changes.

The free model needs clear, detailed prompts.

Prerequisites:
    pip install aider-chat pytest
    export OPENROUTER_API_KEY=sk-or-v1...

Run:
    python run_aider.py --task django__django-11179 --trials 1
    python run_aider.py --trials 1  # all tasks
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pandas as pd


# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

AGENT_NAME   = "Aider"
OUT_DIR      = Path("data/traces/aider")
WORKSPACE    = Path("workspace_aider")
TIMEOUT_SEC  = 300      # 5 minutes
MODEL        = "openrouter/openrouter/free"


# ─────────────────────────────────────────────────────────────────────────────
# Repo helpers
# ─────────────────────────────────────────────────────────────────────────────

def clone_repo(repo: str, commit: str, dest: Path) -> Path:
    """Clone repo with shallow depth."""
    repo_name = repo.split("/")[-1]
    repo_path = dest / repo_name

    if repo_path.exists():
        shutil.rmtree(repo_path)

    repo_url = f"https://github.com/{repo}.git"
    print(f"Clone {repo_url.split('/')[-1]}... ", end="", flush=True)

    result = subprocess.run(
        ["git", "clone", "--depth", "50", repo_url, str(repo_path)],
        capture_output=True, text=True, timeout=60
    )
    
    if result.returncode != 0:
        raise RuntimeError(f"Clone failed")
    
    print("✓ ", end="", flush=True)

    # Checkout commit if provided
    if commit and commit != "placeholder":
        subprocess.run(
            ["git", "checkout", commit],
            cwd=repo_path, capture_output=True, check=False, timeout=30
        )

    return repo_path


def run_tests(repo_path: Path, test_names: list) -> tuple[bool, str]:
    """Run pytest on test list."""
    if not test_names or len(test_names) == 0:
        return True, "No tests"

    # First 2 tests only
    test_names = test_names[:2]

    result = subprocess.run(
        [sys.executable, "-m", "pytest"] + test_names +
        ["-xvs", "--tb=short"],
        cwd=repo_path,
        capture_output=True,
        text=True,
        timeout=60
    )
    
    output = (result.stdout + result.stderr)[-300:]
    return result.returncode == 0, output


def files_changed(repo_path: Path) -> bool:
    """Check if any files changed."""
    result = subprocess.run(
        ["git", "diff", "--name-only"],
        cwd=repo_path, capture_output=True, text=True, timeout=10
    )
    return bool(result.stdout.strip())


# ─────────────────────────────────────────────────────────────────────────────
# Aider runner - WITH BETTER PROMPTS
# ─────────────────────────────────────────────────────────────────────────────

def run_aider(repo_path: Path, problem_statement: str, task_id: str) -> tuple[bool, bool, str]:
    """
    Run Aider with detailed prompt to help free model understand the task.
    Returns (commit_proposed, aider_errored, error_message).
    """
    
    # Build a DETAILED prompt that explains what to do
    # Free models need more guidance
    prompt = f"""You are a code fixer. Your task is to fix this GitHub issue:

ISSUE DESCRIPTION:
{problem_statement[:1200]}

TASK ID: {task_id}

INSTRUCTIONS:
1. Read the issue description carefully
2. Look at the failing tests to understand what needs to be fixed
3. Find the root cause of the problem
4. Make minimal code changes to fix it
5. Run the tests to verify your fix works
6. Do NOT add new features, only fix the issue

Start by exploring the repository structure and understanding the problem.
Then make targeted changes to fix it. Be precise and minimal."""

    # Setup API
    if os.environ.get("OPENROUTER_API_KEY"):
        os.environ["OPENAI_API_KEY"] = os.environ["OPENROUTER_API_KEY"]
        os.environ["OPENAI_API_BASE"] = "https://openrouter.ai/api/v1"
        model_arg = MODEL
    else:
        raise EnvironmentError("Set OPENROUTER_API_KEY")

    # Run Aider with the detailed prompt
    cmd = [
        "aider",
        "--model", model_arg,
        "--message", prompt,
        "--yes",
        "--no-stream",  # Non-streaming (faster)
    ]

    print("Aider... ", end="", flush=True)

    try:
        result = subprocess.run(
            cmd, 
            cwd=repo_path,
            capture_output=True, 
            text=True, 
            timeout=TIMEOUT_SEC,
            env=os.environ.copy()
        )

        output = result.stdout + result.stderr
        
        # Check for errors
        errored = (
            "error" in output.lower() and
            "traceback" in output.lower()
        )
        
        error_msg = output[-300:] if errored else ""
        proposed = files_changed(repo_path)

        return proposed, errored, error_msg

    except subprocess.TimeoutExpired:
        return False, False, "Timeout"


# ─────────────────────────────────────────────────────────────────────────────
# One task, one trial
# ─────────────────────────────────────────────────────────────────────────────

def run_trial(task: dict, trial_num: int) -> dict:
    """Run one trial."""
    task_id   = task["task_id"]
    repo      = task["repo"]
    commit    = task.get("base_commit", "")
    stmt      = task.get("problem_statement", "Fix the issue.")
    
    # Parse test lists
    fail_tests = task.get("fail_tests", [])
    if isinstance(fail_tests, str):
        try:
            fail_tests = json.loads(fail_tests)
        except:
            fail_tests = []
    
    pass_tests = task.get("pass_tests", [])
    if isinstance(pass_tests, str):
        try:
            pass_tests = json.loads(pass_tests)
        except:
            pass_tests = []

    start = time.time()
    intervention_required = False
    commit_proposed       = False
    build_broken          = False
    regression            = False
    success               = False
    error_message         = ""

    try:
        WORKSPACE.mkdir(exist_ok=True)
        repo_path = clone_repo(repo, commit, WORKSPACE)

        # Run Aider with improved prompt
        commit_proposed, errored, error_msg = run_aider(repo_path, stmt, task_id)

        if errored:
            intervention_required = True
            error_message = error_msg
            print("Error")
        elif commit_proposed:
            print("Test... ", end="", flush=True)
            
            # Run tests
            if fail_tests:
                passed, test_output = run_tests(repo_path, fail_tests[:2])
                success = passed
                build_broken = not passed
                if not passed:
                    error_message = test_output[:200]
            else:
                success = True
            
            print("✓")
        else:
            error_message = "No changes"
            print("No changes")

    except subprocess.TimeoutExpired:
        intervention_required = True
        error_message = "Timeout"
        print("Timeout")
    except Exception as e:
        intervention_required = True
        error_message = str(e)[:200]
        print(f"Error: {str(e)[:20]}")
    finally:
        shutil.rmtree(WORKSPACE, ignore_errors=True)

    duration = round(time.time() - start, 1)

    return {
        "agent": AGENT_NAME,
        "task_id": task_id,
        "trial": trial_num,
        "success": success,
        "intervention_required": intervention_required,
        "commit_proposed": commit_proposed,
        "build_broken": build_broken,
        "regression": regression,
        "completed": not intervention_required,
        "duration_seconds": duration,
        "error_message": error_message,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Main loop
# ─────────────────────────────────────────────────────────────────────────────

def run_all(filter_task: str = None, trials: int = 3):
    tasks_path = Path("data/benchmark_tasks.csv")
    if not tasks_path.exists():
        print("ERROR: data/benchmark_tasks.csv not found")
        sys.exit(1)

    tasks_df = pd.read_csv(tasks_path)
    if filter_task:
        tasks_df = tasks_df[tasks_df["task_id"] == filter_task]
        if tasks_df.empty:
            print(f"ERROR: task '{filter_task}' not found")
            sys.exit(1)

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    total = len(tasks_df) * trials
    done  = 0

    print(f"\n🚀 Aider Agent Evaluation")
    print(f"   Model: {MODEL}")
    print(f"   Tasks: {len(tasks_df)} × Trials: {trials} = {total} runs\n")

    for _, task in tasks_df.iterrows():
        task_id = task["task_id"]
        print(f"{'─'*55}")
        print(f"Task: {task_id} ({task['difficulty']})")

        for trial in range(1, trials + 1):
            out_file = OUT_DIR / f"{task_id}_trial_{trial}.json"

            if out_file.exists():
                print(f"  Trial {trial}: Skip")
                done += 1
                continue

            print(f"  Trial {trial}: ", end="", flush=True)
            trace = run_trial(task.to_dict(), trial)

            with open(out_file, "w") as f:
                json.dump(trace, f, indent=2)

            if trace["success"]:
                status = "✅"
            elif trace["intervention_required"]:
                status = "⚠️"
            else:
                status = "❌"
            
            print(f"{status} {trace['duration_seconds']:.0f}s", end="")
            if trace["commit_proposed"]:
                print(" (changes made)")
            else:
                print(" (no changes)")
            done += 1

    print(f"\n{'='*55}")
    print(f"Done! {done}/{total} runs")
    print(f"Output: {OUT_DIR}/")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Aider on SWE-bench tasks")
    parser.add_argument("--task", help="Single task")
    parser.add_argument("--trials", type=int, default=3)
    args = parser.parse_args()
    
    if not os.environ.get("OPENROUTER_API_KEY"):
        print("❌ OPENROUTER_API_KEY not set")
        sys.exit(1)
    
    run_all(filter_task=args.task, trials=args.trials)
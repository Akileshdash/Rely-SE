"""
select_tasks.py
===============
Downloads SWE-bench Lite and selects a balanced subset of 15 tasks
(5 easy, 5 medium, 5 hard) for the RELY-SE evaluation.

Run:
    python select_tasks.py

Output:
    data/benchmark_tasks.csv
    examples/trace_format.json  (schema reference)
"""

import json
import pandas as pd
from pathlib import Path


def estimate_difficulty(row):
    """
    Heuristic difficulty estimate based on:
    - Number of FAIL_TO_PASS tests (more tests = harder)
    - Length of problem statement (longer = more complex)
    - Repo (sympy/matplotlib = harder, requests/flask = easier)
    """
    try:
        fail_tests = json.loads(row['FAIL_TO_PASS']) if isinstance(row['FAIL_TO_PASS'], str) else row['FAIL_TO_PASS']
        n_tests = len(fail_tests)
    except Exception:
        n_tests = 1

    stmt_len = len(str(row.get('problem_statement', '')))

    hard_repos = ['sympy', 'matplotlib', 'scikit-learn', 'astropy', 'sphinx']
    easy_repos = ['requests', 'flask', 'seaborn', 'pyvista']
    repo = str(row.get('repo', '')).lower()

    if any(r in repo for r in hard_repos) or (n_tests >= 3 and stmt_len > 1500):
        return 'hard'
    elif any(r in repo for r in easy_repos) or (n_tests == 1 and stmt_len < 600):
        return 'easy'
    else:
        return 'medium'


def select_tasks(n_easy=5, n_medium=5, n_hard=5):
    """
    Downloads SWE-bench Lite and picks a balanced task subset.
    Falls back to a hardcoded list if download fails.
    """
    Path("data").mkdir(exist_ok=True)

    print("Loading SWE-bench Lite dataset...")
    print("(This downloads ~50MB of metadata the first time)\n")

    try:
        from datasets import load_dataset
        dataset = load_dataset("princeton-nlp/SWE-bench_Lite", split="test")
        df = pd.DataFrame(dataset)
        print(f"Loaded {len(df)} tasks from SWE-bench Lite")

    except Exception as e:
        print(f"WARNING: Could not load from HuggingFace: {e}")
        print("Using fallback hardcoded task list...\n")
        df = _fallback_task_list()

    # Add difficulty column
    df['difficulty'] = df.apply(estimate_difficulty, axis=1)

    print("\nDifficulty distribution:")
    print(df['difficulty'].value_counts().to_string())
    print("\nRepo distribution:")
    print(df['repo'].value_counts().head(10).to_string())

    # Select balanced subset
    # Prefer well-known repos that agents handle well
    preferred_easy   = ['django/django', 'pallets/flask', 'psf/requests']
    preferred_medium = ['django/django', 'matplotlib/matplotlib', 'scikit-learn/scikit-learn']
    preferred_hard   = ['sympy/sympy', 'scikit-learn/scikit-learn', 'matplotlib/matplotlib']

    easy_df   = df[df['difficulty'] == 'easy'].copy()
    medium_df = df[df['difficulty'] == 'medium'].copy()
    hard_df   = df[df['difficulty'] == 'hard'].copy()

    def pick(pool, preferred_repos, n):
        """Pick n tasks, prioritising preferred repos."""
        preferred = pool[pool['repo'].isin(preferred_repos)]
        rest = pool[~pool['repo'].isin(preferred_repos)]
        combined = pd.concat([preferred, rest])
        return combined.head(n)

    selected = pd.concat([
        pick(easy_df,   preferred_easy,   n_easy),
        pick(medium_df, preferred_medium, n_medium),
        pick(hard_df,   preferred_hard,   n_hard),
    ]).drop_duplicates(subset='instance_id')

    # Build clean CSV
    rows = []
    for _, row in selected.iterrows():
        try:
            fail_tests = json.loads(row['FAIL_TO_PASS']) if isinstance(row['FAIL_TO_PASS'], str) else row['FAIL_TO_PASS']
            pass_tests = json.loads(row['PASS_TO_PASS']) if isinstance(row.get('PASS_TO_PASS', '[]'), str) else row.get('PASS_TO_PASS', [])
        except Exception:
            fail_tests = []
            pass_tests = []

        rows.append({
            'task_id':        row['instance_id'],
            'repo':           row['repo'],
            'base_commit':    row.get('base_commit', ''),
            'difficulty':     row['difficulty'],
            'language':       'python',
            'trial_count':    3,
            'fail_tests':     json.dumps(fail_tests),
            'pass_tests':     json.dumps(pass_tests),
            'problem_statement': str(row.get('problem_statement', ''))[:500],  # truncate for CSV
        })

    task_df = pd.DataFrame(rows)
    out_path = Path("data/benchmark_tasks.csv")
    task_df.to_csv(out_path, index=False)

    print(f"\n✅ Selected {len(task_df)} tasks saved to {out_path}")
    print("\nSelected tasks:")
    print(task_df[['task_id', 'repo', 'difficulty']].to_string(index=False))

    _write_trace_format_example()
    return task_df


def _fallback_task_list():
    """
    Hardcoded fallback using known SWE-bench Lite task IDs.
    Use this if the HuggingFace download fails.
    These are real instance IDs from SWE-bench Lite.
    """
    tasks = [
        # Easy – Django (well-structured, good test coverage)
        {"instance_id": "django__django-11049", "repo": "django/django", "base_commit": "placeholder", "FAIL_TO_PASS": '["tests/test_runner/test_discover_runner.py::DiscoverRunnerTests::test_pattern"]', "PASS_TO_PASS": "[]", "problem_statement": "Test runner issue."},
        {"instance_id": "django__django-11905", "repo": "django/django", "base_commit": "placeholder", "FAIL_TO_PASS": '["tests/queryset_pickle/tests.py::PickleTests::test_pickle_prefetch_related_with_values"]', "PASS_TO_PASS": "[]", "problem_statement": "Queryset pickle issue."},
        {"instance_id": "django__django-12284", "repo": "django/django", "base_commit": "placeholder", "FAIL_TO_PASS": '["tests/migrations/test_writer.py::WriterTests::test_serialize_class_based_validators"]', "PASS_TO_PASS": "[]", "problem_statement": "Migration writer issue."},
        {"instance_id": "django__django-12700", "repo": "django/django", "base_commit": "placeholder", "FAIL_TO_PASS": '["tests/admin_views/tests.py::AdminViewBasicTestCase::test_change_list_query_string"]', "PASS_TO_PASS": "[]", "problem_statement": "Admin view issue."},
        {"instance_id": "django__django-13590", "repo": "django/django", "base_commit": "placeholder", "FAIL_TO_PASS": '["tests/queryset_pickle/tests.py::PickleTests::test_pickle_exists"]', "PASS_TO_PASS": "[]", "problem_statement": "ORM issue."},
        # Medium – Django/Matplotlib
        {"instance_id": "django__django-14016", "repo": "django/django", "base_commit": "placeholder", "FAIL_TO_PASS": '["tests/auth_tests/test_forms.py::AuthenticationFormTests::test_username_field_max_length_defaults_to_254", "tests/auth_tests/test_forms.py::AuthenticationFormTests::test_username_field_max_length_honors_custom_user_model"]', "PASS_TO_PASS": "[]", "problem_statement": "Auth form issue."},
        {"instance_id": "django__django-14017", "repo": "django/django", "base_commit": "placeholder", "FAIL_TO_PASS": '["tests/template_tests/filter_tests/test_truncatechars.py"]', "PASS_TO_PASS": "[]", "problem_statement": "Template filter issue."},
        {"instance_id": "matplotlib__matplotlib-22711", "repo": "matplotlib/matplotlib", "base_commit": "placeholder", "FAIL_TO_PASS": '["lib/matplotlib/tests/test_axes.py::test_bar_label_location_vertical"]', "PASS_TO_PASS": "[]", "problem_statement": "Axes bar label issue."},
        {"instance_id": "matplotlib__matplotlib-22835", "repo": "matplotlib/matplotlib", "base_commit": "placeholder", "FAIL_TO_PASS": '["lib/matplotlib/tests/test_figure.py::test_clf_not_redefined"]', "PASS_TO_PASS": "[]", "problem_statement": "Figure clf issue."},
        {"instance_id": "scikit-learn__scikit-learn-10297", "repo": "scikit-learn/scikit-learn", "base_commit": "placeholder", "FAIL_TO_PASS": '["sklearn/tests/test_pipeline.py::test_pipeline_memory"]', "PASS_TO_PASS": "[]", "problem_statement": "Pipeline memory issue."},
        # Hard – Sympy/Scikit-learn
        {"instance_id": "sympy__sympy-12481", "repo": "sympy/sympy", "base_commit": "placeholder", "FAIL_TO_PASS": '["sympy/combinatorics/tests/test_permutations.py::test_Permutation", "sympy/combinatorics/tests/test_permutations.py::test_args"]', "PASS_TO_PASS": "[]", "problem_statement": "Combinatorics permutation issue."},
        {"instance_id": "sympy__sympy-13043", "repo": "sympy/sympy", "base_commit": "placeholder", "FAIL_TO_PASS": '["sympy/integrals/tests/test_integrals.py::test_issue_12645", "sympy/integrals/tests/test_integrals.py::test_issue_13046"]', "PASS_TO_PASS": "[]", "problem_statement": "Integral evaluation issue."},
        {"instance_id": "sympy__sympy-16988", "repo": "sympy/sympy", "base_commit": "placeholder", "FAIL_TO_PASS": '["sympy/sets/tests/test_sets.py::test_issue_16988"]', "PASS_TO_PASS": "[]", "problem_statement": "Sets module issue."},
        {"instance_id": "scikit-learn__scikit-learn-13142", "repo": "scikit-learn/scikit-learn", "base_commit": "placeholder", "FAIL_TO_PASS": '["sklearn/linear_model/tests/test_ridge.py::test_ridge_regression_sample_weight", "sklearn/linear_model/tests/test_ridge.py::test_ridge_shapes"]', "PASS_TO_PASS": "[]", "problem_statement": "Ridge regression issue."},
        {"instance_id": "scikit-learn__scikit-learn-14894", "repo": "scikit-learn/scikit-learn", "base_commit": "placeholder", "FAIL_TO_PASS": '["sklearn/tests/test_common.py::test_estimators_nan_inf"]', "PASS_TO_PASS": "[]", "problem_statement": "Estimator NaN handling issue."},
    ]
    df = pd.DataFrame(tasks)
    return df


def _write_trace_format_example():
    """Write a reference JSON showing the expected trace format."""
    Path("examples").mkdir(exist_ok=True)
    example = {
        "agent": "Aider",
        "task_id": "django__django-11049",
        "trial": 1,
        "success": True,
        "intervention_required": False,
        "commit_proposed": True,
        "build_broken": False,
        "regression": False,
        "completed": True,
        "duration_seconds": 142.3,
        "error_message": ""
    }
    with open("examples/trace_format.json", "w") as f:
        json.dump(example, f, indent=2)
    print("\n✅ Trace format example written to examples/trace_format.json")


if __name__ == "__main__":
    select_tasks()

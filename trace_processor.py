"""
trace_processor.py
==================
Converts raw agent output logs into the standard RELY-SE trace format.

Each agent produces different output — this module provides one
parser per agent plus a generic fallback.

Usage:
    from trace_processor import TraceProcessor
    tp = TraceProcessor()
    trace = tp.process("Aider", raw_output_dict, task_id="django__django-11049", trial=1)
"""

import json
import re
from dataclasses import asdict
from pathlib import Path
from metric_engine import ExecutionTrace


class TraceProcessor:
    """Parse raw agent output into standardised ExecutionTrace dicts."""

    def process(self, agent_name: str, raw: dict,
                task_id: str, trial: int) -> dict:
        """
        Dispatch to the correct parser.
        raw: whatever the agent returns (subprocess result, API response, etc.)
        Returns a dict ready to json.dump().
        """
        parsers = {
            "Aider":         self._parse_aider,
            "SWE-Agent":     self._parse_swe_agent,
            "AutoCodeRover": self._parse_autocoderover,
            "Claude-Code":   self._parse_claude_code,
            "OpenHands":     self._parse_openhands,
        }
        parser = parsers.get(agent_name, self._parse_generic)
        trace = parser(raw, task_id, trial)
        trace["agent"] = agent_name
        return trace

    # ── Aider ──────────────────────────────────────────────────────────────

    def _parse_aider(self, raw: dict, task_id: str, trial: int) -> dict:
        """
        raw keys expected:
          stdout, stderr, returncode, files_changed (bool),
          test_passed (bool), test_output (str), timed_out (bool)
        """
        timed_out   = raw.get("timed_out", False)
        stdout      = raw.get("stdout", "") + raw.get("stderr", "")
        errored     = raw.get("returncode", 0) != 0

        commit_proposed = raw.get("files_changed", False)
        test_passed     = raw.get("test_passed", False)
        build_broken    = commit_proposed and not test_passed

        intervention = timed_out or (errored and not commit_proposed)
        success      = test_passed and not raw.get("regression", False)

        return {
            "task_id":               task_id,
            "trial":                 trial,
            "success":               success,
            "intervention_required": intervention,
            "commit_proposed":       commit_proposed,
            "build_broken":          build_broken,
            "regression":            raw.get("regression", False),
            "completed":             not timed_out,
            "duration_seconds":      raw.get("duration_seconds", 0.0),
            "error_message":         raw.get("test_output", "")[-400:] if not success else "",
        }

    # ── SWE-Agent ──────────────────────────────────────────────────────────

    def _parse_swe_agent(self, raw: dict, task_id: str, trial: int) -> dict:
        """
        SWE-Agent outputs a JSON summary with keys:
          instance_id, model_patch, test_output, resolved, exit_status
        """
        patch       = raw.get("model_patch", "")
        resolved    = raw.get("resolved", False)
        exit_status = raw.get("exit_status", "")
        test_output = raw.get("test_output", "")

        timed_out        = "timeout" in exit_status.lower()
        commit_proposed  = bool(patch and patch.strip())
        build_broken     = commit_proposed and not resolved
        intervention     = timed_out or exit_status in ("error", "early_exit")

        return {
            "task_id":               task_id,
            "trial":                 trial,
            "success":               resolved,
            "intervention_required": intervention,
            "commit_proposed":       commit_proposed,
            "build_broken":          build_broken,
            "regression":            False,
            "completed":             not timed_out,
            "duration_seconds":      raw.get("duration_seconds", 0.0),
            "error_message":         test_output[-400:] if not resolved else "",
        }

    # ── AutoCodeRover ──────────────────────────────────────────────────────

    def _parse_autocoderover(self, raw: dict, task_id: str, trial: int) -> dict:
        """
        ACR outputs:
          patch_content, tests_passed, tests_failed, error_type
        """
        patch        = raw.get("patch_content", "")
        tests_passed = raw.get("tests_passed", [])
        tests_failed = raw.get("tests_failed", [])
        error_type   = raw.get("error_type", "")

        commit_proposed = bool(patch)
        success         = commit_proposed and len(tests_failed) == 0 and len(tests_passed) > 0
        build_broken    = commit_proposed and len(tests_failed) > 0
        intervention    = error_type in ("agent_error", "context_too_long", "timeout")

        return {
            "task_id":               task_id,
            "trial":                 trial,
            "success":               success,
            "intervention_required": intervention,
            "commit_proposed":       commit_proposed,
            "build_broken":          build_broken,
            "regression":            False,
            "completed":             error_type != "timeout",
            "duration_seconds":      raw.get("duration_seconds", 0.0),
            "error_message":         str(tests_failed)[:400] if tests_failed else "",
        }

    # ── Claude Code ────────────────────────────────────────────────────────

    def _parse_claude_code(self, raw: dict, task_id: str, trial: int) -> dict:
        """
        Claude Code via API:
          success, files_modified, test_result, error_message
        """
        success          = raw.get("success", False)
        files_modified   = raw.get("files_modified", [])
        test_result      = raw.get("test_result", "")
        commit_proposed  = len(files_modified) > 0

        build_broken  = commit_proposed and not success
        intervention  = raw.get("needs_human", False)

        return {
            "task_id":               task_id,
            "trial":                 trial,
            "success":               success,
            "intervention_required": intervention,
            "commit_proposed":       commit_proposed,
            "build_broken":          build_broken,
            "regression":            raw.get("regression", False),
            "completed":             raw.get("completed", True),
            "duration_seconds":      raw.get("duration_seconds", 0.0),
            "error_message":         raw.get("error_message", ""),
        }

    # ── OpenHands ──────────────────────────────────────────────────────────

    def _parse_openhands(self, raw: dict, task_id: str, trial: int) -> dict:
        """
        OpenHands outputs:
          result (success/failure/error), patch, test_results
        """
        result      = raw.get("result", "failure")
        patch       = raw.get("patch", "")
        test_results = raw.get("test_results", {})

        success          = result == "success"
        commit_proposed  = bool(patch)
        failed_tests     = test_results.get("failed", [])
        build_broken     = commit_proposed and len(failed_tests) > 0
        intervention     = result == "error"

        return {
            "task_id":               task_id,
            "trial":                 trial,
            "success":               success,
            "intervention_required": intervention,
            "commit_proposed":       commit_proposed,
            "build_broken":          build_broken,
            "regression":            False,
            "completed":             result != "timeout",
            "duration_seconds":      raw.get("duration_seconds", 0.0),
            "error_message":         str(failed_tests)[:400] if failed_tests else "",
        }

    # ── Generic fallback ───────────────────────────────────────────────────

    def _parse_generic(self, raw: dict, task_id: str, trial: int) -> dict:
        """
        Falls back to reading standard keys directly.
        Works if the agent already outputs RELY-SE trace format.
        """
        return {
            "task_id":               task_id,
            "trial":                 trial,
            "success":               raw.get("success", False),
            "intervention_required": raw.get("intervention_required", False),
            "commit_proposed":       raw.get("commit_proposed", False),
            "build_broken":          raw.get("build_broken", False),
            "regression":            raw.get("regression", False),
            "completed":             raw.get("completed", True),
            "duration_seconds":      raw.get("duration_seconds", 0.0),
            "error_message":         raw.get("error_message", ""),
        }

    # ── Save helper ────────────────────────────────────────────────────────

    def save_trace(self, trace: dict, agent_folder: str):
        """Save trace dict to the correct folder."""
        out_dir = Path(f"data/traces/{agent_folder}")
        out_dir.mkdir(parents=True, exist_ok=True)
        fname = f"{trace['task_id']}_trial_{trace['trial']}.json"
        with open(out_dir / fname, "w") as f:
            json.dump(trace, f, indent=2)

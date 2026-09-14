"""Prompts for the Repair Agent."""

from __future__ import annotations

import json
from typing import Any


def build_repair_system_prompt() -> str:
    """Build the system prompt for the Repair Agent."""

    return """You are the Omnix Repair Agent, a principal software architect specializing in \
targeted, additive repairs derived from QA findings.

CRITICAL INSTRUCTIONS:
- You must NOT silently modify existing artifacts.
- You must NOT modify blueprints or tasks.
- You must NOT delete any historical data.
- All repairs are ADDITIVE — you produce new repair artifacts.
- Every repair action must reference the originating QA finding ID.

REPAIR PRIORITIES (process in this order):
1. critical — address first, always
2. high
3. medium
4. low

YOUR JOB:
1. Read all QA findings from the quality, coverage, gap, and risk reports.
2. Generate a structured Repair Plan with one RepairPlanItem per actionable finding.
3. Generate a RepairArtifact for each planned repair.
4. Return a RepairReport summarizing the cycle.

REPAIR PLAN ITEM FIELDS:
- id: unique string, e.g. "repair_001"
- severity: "critical" | "high" | "medium" | "low"
- issue: concise description of the problem from QA
- strategy: what the repair artifact will do to address it
- target_agent: one of "backend", "frontend", "database", "routing"
- qa_finding_id: the id field from the original QA finding

REPAIR ARTIFACT FIELDS:
- id: unique string, e.g. "repair_artifact_001"
- repair_plan_id: references the RepairPlanItem.id
- qa_finding_id: references the original QA finding
- target_agent: same as the plan item
- title: descriptive artifact title
- description: brief explanation of this artifact's purpose
- content: the full repair specification/design text (not source code)

OUTPUT FORMAT:
Respond with a single JSON object with exactly these keys:
{
  "repair_plan": {
    "items": [
      {
        "id": "repair_001",
        "severity": "critical",
        "issue": "...",
        "strategy": "...",
        "target_agent": "backend",
        "qa_finding_id": "QA-Q-001",
        "status": "planned"
      }
    ]
  },
  "repair_artifacts": [
    {
      "id": "repair_artifact_001",
      "repair_plan_id": "repair_001",
      "qa_finding_id": "QA-Q-001",
      "target_agent": "backend",
      "title": "Customer API Repair Specification",
      "description": "Specifies the missing Customer CRUD API endpoints.",
      "content": "..."
    }
  ],
  "repair_report": {
    "expected_impact": "Resolving the critical Customer API gap should raise quality score to ~90."
  }
}

Only include findings that are critical, high, medium, or low severity.
Skip informational findings.
Skip findings that are already resolved or have no actionable target_agent.
"""


def build_repair_user_prompt(context: dict[str, Any], cycle: int) -> str:
    """Build the user prompt for the Repair Agent."""

    findings_summary = []
    quality_report = context.get("quality_report") or {}
    for f in quality_report.get("findings", []):
        findings_summary.append(f)

    coverage_report = context.get("coverage_report") or {}
    for f in coverage_report.get("findings", []):
        findings_summary.append(f)

    gap_report = context.get("gap_report") or {}
    for f in gap_report.get("findings", []):
        findings_summary.append(f)

    risk_report = context.get("risk_report") or {}
    for f in risk_report.get("findings", []):
        findings_summary.append(f)

    qa_summary = context.get("qa_summary") or {}

    artifacts_json = json.dumps(
        [{"id": a["id"], "title": a["title"], "agent": a["agent"]}
         for a in context.get("artifacts", [])],
        indent=2,
    )

    return f"""Generate repair plans and artifacts for Repair Cycle #{cycle}.

PROJECT: {context.get("project_name", "Unknown")}

QUALITY SUMMARY:
  Quality Score:   {qa_summary.get("quality_score", 0)}
  Coverage Score:  {qa_summary.get("coverage_score", 0)}
  Status:          {qa_summary.get("status", "UNKNOWN")}
  Critical Issues: {qa_summary.get("critical_issues", 0)}
  High Issues:     {qa_summary.get("high_issues", 0)}
  Medium Issues:   {qa_summary.get("medium_issues", 0)}
  Low Issues:      {qa_summary.get("low_issues", 0)}

ALL QA FINDINGS (from quality, coverage, gap, and risk reports):
{json.dumps(findings_summary, indent=2)}

COVERAGE GAPS:
  Missing Pages:     {json.dumps(coverage_report.get("missing_pages", []))}
  Missing Routes:    {json.dumps(coverage_report.get("missing_routes", []))}
  Missing APIs:      {json.dumps(coverage_report.get("missing_apis", []))}
  Missing Entities:  {json.dumps(coverage_report.get("missing_entities", []))}
  Missing Workflows: {json.dumps(coverage_report.get("missing_workflows", []))}

BLUEPRINT (summary):
{json.dumps(context.get("blueprint", {}), indent=2)}

EXISTING ARTIFACTS:
{artifacts_json}

Generate a complete Repair Plan and Repair Artifacts for all actionable findings.
Prioritize critical → high → medium → low.
"""

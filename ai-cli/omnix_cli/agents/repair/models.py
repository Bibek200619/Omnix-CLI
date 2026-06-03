"""Internal models for the Repair Agent."""

from __future__ import annotations

from pydantic import BaseModel

from omnix_cli.schemas.repair import (
    RepairArtifact,
    RepairPlan,
    RepairReport,
)


class RepairAgentResult(BaseModel):
    """The complete output of one repair cycle."""

    provider: str
    model: str
    cycle: int
    repair_plan: RepairPlan
    repair_artifacts: list[RepairArtifact]
    repair_report: RepairReport

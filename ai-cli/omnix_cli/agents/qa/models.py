"""Internal models for the QA Agent."""

from __future__ import annotations

from pydantic import BaseModel

from omnix_cli.schemas.qa import (
    CoverageReport,
    GapReport,
    QASummary,
    QualityReport,
    RiskReport,
)


class QAAgentResult(BaseModel):
    """The complete set of reports produced by the QA Agent."""

    provider: str
    model: str
    summary: QASummary
    quality_report: QualityReport
    coverage_report: CoverageReport
    gap_report: GapReport
    risk_report: RiskReport

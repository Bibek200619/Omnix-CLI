"""Schemas for the QA Agent and Quality Reports."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class QASeverity(StrEnum):
    """Severity of a detected QA issue."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


class QAStatus(StrEnum):
    """Overall quality status of the project."""

    PASSED = "PASSED"
    ACCEPTABLE = "ACCEPTABLE"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    FAILED = "FAILED"


class QAFinding(BaseModel):
    """A specific finding from the QA process."""

    id: str
    title: str
    description: str
    severity: QASeverity
    category: str  # e.g., "Architecture", "Coverage", "Consistency", "Risk"
    explanation: str


class QualityReport(BaseModel):
    """High-level quality evaluation of the project."""

    model_config = ConfigDict(extra="forbid")

    project_name: str
    timestamp: datetime = Field(default_factory=datetime.now)
    version: int = 1
    overall_score: int = 0
    critical_issues: int = 0
    high_issues: int = 0
    medium_issues: int = 0
    low_issues: int = 0
    findings: list[QAFinding] = Field(default_factory=list)
    status: QAStatus = QAStatus.REVIEW_REQUIRED
    summary: str = ""


class CoverageReport(BaseModel):
    """Detailed analysis of implementation coverage."""

    model_config = ConfigDict(extra="forbid")

    project_name: str
    timestamp: datetime = Field(default_factory=datetime.now)
    version: int = 1
    coverage_score: int = 0
    missing_pages: list[str] = Field(default_factory=list)
    missing_routes: list[str] = Field(default_factory=list)
    missing_apis: list[str] = Field(default_factory=list)
    missing_entities: list[str] = Field(default_factory=list)
    missing_workflows: list[str] = Field(default_factory=list)
    findings: list[QAFinding] = Field(default_factory=list)


class GapReport(BaseModel):
    """Analysis of architectural and functional gaps."""

    model_config = ConfigDict(extra="forbid")

    project_name: str
    timestamp: datetime = Field(default_factory=datetime.now)
    version: int = 1
    gap_score: int = 0
    findings: list[QAFinding] = Field(default_factory=list)


class RiskReport(BaseModel):
    """Analysis of project risks."""

    model_config = ConfigDict(extra="forbid")

    project_name: str
    timestamp: datetime = Field(default_factory=datetime.now)
    version: int = 1
    risk_score: int = 0
    findings: list[QAFinding] = Field(default_factory=list)


class QASummary(BaseModel):
    """A lightweight summary of the QA state."""

    model_config = ConfigDict(extra="forbid")

    project_name: str
    timestamp: datetime = Field(default_factory=datetime.now)
    version: int = 1
    quality_score: int
    coverage_score: int
    gap_score: int
    risk_score: int
    critical_issues: int
    high_issues: int
    medium_issues: int
    low_issues: int
    status: QAStatus

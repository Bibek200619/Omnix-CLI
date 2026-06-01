"""QA audit schemas.

These schemas are defined in Phase 0 so future QA output has a stable contract.
Execution of QA audits is deferred until Phase 8.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from omnix_cli.schemas.tasks import AgentRole


class AuditErrorType(StrEnum):
    """Supported QA audit categories."""

    SCHEMA_MISMATCH = "schema_mismatch"
    ROUTE_CONFLICT = "route_conflict"
    API_CONTRACT_MISMATCH = "api_contract_mismatch"
    FILE_CONFLICT = "file_conflict"
    MISSING_DEPENDENCY = "missing_dependency"
    MIGRATION_ERROR = "migration_error"


class AuditFinding(BaseModel):
    """Single structured QA finding."""

    model_config = ConfigDict(extra="forbid")

    error_type: AuditErrorType
    affected_agents: list[AgentRole] = Field(default_factory=list)
    details: str = ""
    blocking: bool = True


class AuditReport(BaseModel):
    """Structured QA audit output."""

    model_config = ConfigDict(extra="forbid")

    passed: bool = True
    findings: list[AuditFinding] = Field(default_factory=list)

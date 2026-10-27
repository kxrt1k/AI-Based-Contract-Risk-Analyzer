
from typing import Literal
from pydantic import BaseModel, Field


RiskLevel = Literal["low", "medium", "high", "critical"]


class Finding(BaseModel):
    clause_type: str
    risk_level: RiskLevel
    confidence: float = Field(
        ge=0,
        le=1,
        description="Rule/model confidence, not probability of loss",
    )
    evidence: str
    reason: str
    recommendation: str
    source: Literal["rules", "legalbert"] = "rules"


class ClauseClassification(BaseModel):
    text: str
    label: str
    confidence: float = Field(ge=0, le=1)


class ContractStatistics(BaseModel):
    word_count: int
    clauses_detected: int
    high_risk_clauses: int
    critical_risk_clauses: int


class AnalyzeRequest(BaseModel):
    text: str = Field(min_length=1, max_length=1_000_000)
    contract_type: str = "general"


class AnalyzeResponse(BaseModel):
    schema_version: str = "1.1"
    contract_type: str
    overall_risk_score: int = Field(ge=0, le=100)
    risk_level: RiskLevel
    summary: str
    statistics: ContractStatistics
    findings: list[Finding]
    missing_clause_checks: list[str]
    clause_classifications: list[ClauseClassification] = Field(
        default_factory=list
    )
    disclaimer: str = (
        "AI-assisted screening only. Not legal advice. "
        "Have a qualified legal professional review important contracts."
    )

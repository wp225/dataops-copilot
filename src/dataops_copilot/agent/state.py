from pydantic import BaseModel, Field
from typing import Literal
from datetime import datetime, UTC
from dataops_copilot.quality.models import QualityReport, DataQualityIncident

class IncidentInvestigationRequest(BaseModel):
    incident: DataQualityIncident
    quality_report: QualityReport
    dataset_name: str
    batch_id: str
    requested_at: datetime = Field(default_factory=lambda : datetime.now(UTC))

class RCAReport(BaseModel):
    likely_cause: str
    confidence: Literal['low', 'medium', 'high']
    explination: str
    previous_similar_encounter: int
    evidence: list[str]
    analysis_executed: list[str]
    escelation: bool
    recommendation: str
    
class IncidentRCAreport(BaseModel):
    incident: DataQualityIncident
    date: datetime = Field(default_factory=lambda: datetime.now(UTC))
    report: RCAReport
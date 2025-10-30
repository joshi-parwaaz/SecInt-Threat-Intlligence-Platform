"""
models.py - Pydantic models for API request/response validation
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class ThreatType(str, Enum):
    CREDENTIAL_LEAK = "credential_leak"
    EXPLOIT = "exploit"
    PHISHING = "phishing"
    MALWARE = "malware"
    UNKNOWN = "unknown"

class DatasetSource(str, Enum):
    OPEN_MALSEC = "open_malsec"
    MALWARE_MOTIF = "malware_motif"
    PHISHING_EMAILS = "phishing_emails"
    EXPLOITDB = "exploitdb"

class ThreatRecord(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    dataset: DatasetSource
    threat_type: ThreatType
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[dict] = None
    classification_confidence: Optional[float] = None

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "dataset": "open_malsec",
                "threat_type": "malware",
                "content": "Ransomware campaign detected...",
                "classification_confidence": 0.92
            }
        }

class IngestionLog(BaseModel):
    dataset: str
    records_processed: int
    records_failed: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: str

class AnalyticsSummary(BaseModel):
    total_threats: int
    threats_by_type: dict
    threats_by_dataset: dict
    recent_threats: List[ThreatRecord]
    last_updated: datetime = Field(default_factory=datetime.utcnow)

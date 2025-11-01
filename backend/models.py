"""
models.py - Pydantic models for API request/response validation
SecInt v2 - Real-time threat intelligence platform
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum

class ThreatType(str, Enum):
    CREDENTIAL_LEAK = "credential_leak"
    EXPLOIT = "exploit"
    PHISHING = "phishing"
    MALWARE = "malware"
    RANSOMWARE = "ransomware"
    BOTNET = "botnet"
    C2 = "c2"
    UNKNOWN = "unknown"

class IOCType(str, Enum):
    IPV4 = "ipv4"
    DOMAIN = "domain"
    URL = "url"
    MD5 = "md5"
    SHA1 = "sha1"
    SHA256 = "sha256"
    CVE = "cve"
    EMAIL = "email"

class SeverityLevel(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"

class ThreatSource(str, Enum):
    OTX = "otx"
    URLHAUS = "urlhaus"
    ABUSEIPDB = "abuseipdb"
    VIRUSTOTAL = "virustotal"
    MANUAL = "manual"

class IOCRecord(BaseModel):
    """Indicator of Compromise record"""
    id: Optional[str] = Field(default=None, alias="_id")
    ioc_value: str
    ioc_type: IOCType
    source: ThreatSource
    severity: SeverityLevel = SeverityLevel.UNKNOWN
    severity_score: int = 0
    severity_reasons: List[str] = []
    
    # Enrichment data
    malware_family: Optional[str] = None
    threat_type: Optional[ThreatType] = None
    context: Optional[str] = None
    description: Optional[str] = None
    
    # Detection metrics
    vt_detection_rate: Optional[float] = None
    vt_detections: Optional[str] = None
    abuse_score: Optional[int] = None
    # Additional metadata and correlation
    correlation_id: Optional[str] = None
    ioc_category: Optional[str] = None
    threat_actor: Optional[str] = None
    last_updated: Optional[datetime] = None
    
    # Metadata
    first_seen: datetime = Field(default_factory=datetime.utcnow)
    last_seen: Optional[datetime] = None
    enrichment_timestamp: Optional[datetime] = None
    sources: Dict = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    
    # URLhaus specific
    url_status: Optional[str] = None
    threat: Optional[str] = None
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "ioc_value": "45.61.49.78",
                "ioc_type": "ipv4",
                "source": "urlhaus",
                "severity": "CRITICAL",
                "severity_score": 85,
                "malware_family": "Emotet",
                "vt_detections": "47/70"
            }
        }

class ThreatPulse(BaseModel):
    """Threat intelligence pulse from OTX"""
    id: Optional[str] = Field(default=None, alias="_id")
    pulse_id: str
    name: str
    description: Optional[str] = None
    author_name: str
    created: datetime
    modified: datetime
    tlp: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    references: List[str] = Field(default_factory=list)
    indicators: List[Dict] = Field(default_factory=list)
    extracted_iocs: List[str] = Field(default_factory=list)
    
    class Config:
        populate_by_name = True

class URLhausThreat(BaseModel):
    """Malware URL from URLhaus"""
    id: Optional[str] = Field(default=None, alias="_id")
    urlhaus_id: str
    url: str
    url_status: str
    host: str
    date_added: str
    threat: str
    tags: List[str] = Field(default_factory=list)
    reporter: Optional[str] = None
    extracted_iocs: List[str] = Field(default_factory=list)
    
    class Config:
        populate_by_name = True

class IngestionLog(BaseModel):
    """Ingestion process log"""
    source: str
    records_processed: int
    records_failed: int
    iocs_extracted: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: str
    error_message: Optional[str] = None

class IOCStats(BaseModel):
    """IOC statistics"""
    total_iocs: int
    by_type: Dict[str, int]
    by_severity: Dict[str, int]
    by_source: Dict[str, int]
    critical_count: int
    high_count: int
    recent_count: int
    last_updated: datetime = Field(default_factory=datetime.utcnow)

class IOCSearchQuery(BaseModel):
    """IOC search query parameters"""
    query: Optional[str] = None
    ioc_type: Optional[IOCType] = None
    severity: Optional[SeverityLevel] = None
    source: Optional[ThreatSource] = None
    limit: int = 50
    offset: int = 0

class IOCExportRequest(BaseModel):
    """IOC export request"""
    format: str = "json"  # json or csv
    severity: Optional[SeverityLevel] = None
    ioc_type: Optional[IOCType] = None
    limit: int = 1000

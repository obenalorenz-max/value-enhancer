from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime


class TargetType(str, Enum):
    USERNAME = "username"
    PHONE = "phone"
    DOMAIN = "domain"
    SECRETS = "secrets"
    METADATA = "metadata"
    EMAIL = "email"
    FULL = "full"


class IdentityFinding(BaseModel):
    platform: str
    url: str
    exists: bool
    status_code: int
    response_time_ms: float
    category: str = "general"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PhoneFinding(BaseModel):
    raw_input: str
    valid: bool
    possible: bool
    e164: Optional[str] = None
    international: Optional[str] = None
    national: Optional[str] = None
    country_code: Optional[int] = None
    region_code: Optional[str] = None
    location: Optional[str] = None
    carrier: Optional[str] = None
    line_type: Optional[str] = None
    timezone: Optional[str] = None
    google_dorks: List[str] = Field(default_factory=list)


class SecretSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class SecretFinding(BaseModel):
    file_path: str
    line_number: int
    rule_id: str
    description: str
    matched_snippet: str
    entropy: float
    severity: SecretSeverity


class DomainFinding(BaseModel):
    domain: str
    ip_addresses: List[str] = Field(default_factory=list)
    ipv6_addresses: List[str] = Field(default_factory=list)
    mx_records: List[str] = Field(default_factory=list)
    txt_records: List[str] = Field(default_factory=list)
    name_servers: List[str] = Field(default_factory=list)
    spf_record: Optional[str] = None
    dmarc_record: Optional[str] = None
    email_spoofable: bool = False
    discovered_subdomains: List[str] = Field(default_factory=list)


class MetadataFinding(BaseModel):
    filename: str
    file_size_bytes: int
    has_exif: bool
    make: Optional[str] = None
    model: Optional[str] = None
    software: Optional[str] = None
    datetime_original: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    altitude: Optional[float] = None
    maps_link: Optional[str] = None
    raw_tags: Dict[str, str] = Field(default_factory=dict)


class IntelligenceReport(BaseModel):
    target: str
    target_type: TargetType
    generated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    execution_time_seconds: float = 0.0
    summary: Dict[str, Any] = Field(default_factory=dict)
    identity_results: List[IdentityFinding] = Field(default_factory=list)
    phone_results: Optional[PhoneFinding] = None
    secret_results: List[SecretFinding] = Field(default_factory=list)
    domain_results: Optional[DomainFinding] = None
    metadata_results: List[MetadataFinding] = Field(default_factory=list)
    risk_score: int = Field(default=0, ge=0, le=100)
    risk_factors: List[str] = Field(default_factory=list)

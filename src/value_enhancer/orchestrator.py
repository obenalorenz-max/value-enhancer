import os
import time
from typing import Optional, List
from .models import (
    TargetType,
    IntelligenceReport,
)
from .modules.identity import IdentityHunter
from .modules.phone import PhoneHunter
from .modules.secrets import SecretHunter
from .modules.domain import DomainHunter
from .modules.metadata import MetadataHunter


class ReconOrchestrator:
    """Central OSINT & Intelligence Orchestrator (SpiderFoot-style correlation engine)."""

    def __init__(self):
        self.identity_hunter = IdentityHunter()
        self.phone_hunter = PhoneHunter()
        self.secret_hunter = SecretHunter()
        self.domain_hunter = DomainHunter()
        self.metadata_hunter = MetadataHunter()

    async def scan_username(self, username: str) -> IntelligenceReport:
        start_time = time.monotonic()
        results = await self.identity_hunter.scan(username)
        duration = round(time.monotonic() - start_time, 2)

        found_accounts = [r for r in results if r.exists]
        risk_score = min(len(found_accounts) * 8, 90)

        risk_factors: List[str] = []
        if len(found_accounts) > 5:
            risk_factors.append(
                f"High digital footprint: Discovered {len(found_accounts)} active public accounts matching target handle."
            )
        dev_accounts = [r for r in found_accounts if r.category == "developer"]
        if dev_accounts:
            risk_factors.append(
                f"Developer profile exposure detected ({len(dev_accounts)} platforms). Potential source code / commit leaks."
            )

        report = IntelligenceReport(
            target=username,
            target_type=TargetType.USERNAME,
            execution_time_seconds=duration,
            summary={
                "total_probed": len(results),
                "total_found": len(found_accounts),
                "platforms_found": [r.platform for r in found_accounts],
            },
            identity_results=results,
            risk_score=risk_score,
            risk_factors=risk_factors,
        )
        return report

    def scan_phone(self, phone_number: str, region: str = "CA") -> IntelligenceReport:
        start_time = time.monotonic()
        finding = self.phone_hunter.scan(phone_number, default_region=region)
        duration = round(time.monotonic() - start_time, 2)

        risk_score = 10
        risk_factors: List[str] = []
        if finding.valid:
            risk_score += 25
            if finding.line_type == "Mobile":
                risk_factors.append("Active mobile SIM line identified. Highly susceptible to targeted SMS phishing.")
            elif "VOIP" in (finding.line_type or ""):
                risk_factors.append("Virtual/VOIP burner line detected. Common indicator of anonymous account usage.")

            if finding.carrier:
                risk_factors.append(f"Carrier identified as {finding.carrier} ({finding.location or finding.region_code}).")

        report = IntelligenceReport(
            target=phone_number,
            target_type=TargetType.PHONE,
            execution_time_seconds=duration,
            summary={
                "valid": finding.valid,
                "e164": finding.e164,
                "carrier": finding.carrier,
                "line_type": finding.line_type,
            },
            phone_results=finding,
            risk_score=risk_score,
            risk_factors=risk_factors,
        )
        return report

    async def scan_domain(self, domain: str) -> IntelligenceReport:
        start_time = time.monotonic()
        finding = await self.domain_hunter.scan(domain)
        duration = round(time.monotonic() - start_time, 2)

        risk_score = 20
        risk_factors: List[str] = []
        if finding.email_spoofable:
            risk_score += 40
            risk_factors.append("CRITICAL: Domain lacks strict DMARC enforcement (email spoofing/phishing possible).")
        if len(finding.discovered_subdomains) > 3:
            risk_score += 20
            risk_factors.append(f"Expanded attack surface: {len(finding.discovered_subdomains)} active subdomains discovered.")

        report = IntelligenceReport(
            target=domain,
            target_type=TargetType.DOMAIN,
            execution_time_seconds=duration,
            summary={
                "ips": finding.ip_addresses,
                "spoofable": finding.email_spoofable,
                "subdomains_count": len(finding.discovered_subdomains),
            },
            domain_results=finding,
            risk_score=min(risk_score, 100),
            risk_factors=risk_factors,
        )
        return report

    def scan_secrets(self, path_or_text: str, is_text: bool = False) -> IntelligenceReport:
        start_time = time.monotonic()
        if is_text:
            findings = self.secret_hunter.scan_text(path_or_text)
            target_name = "raw_snippet"
        else:
            findings = self.secret_hunter.scan_path(path_or_text)
            target_name = path_or_text
        duration = round(time.monotonic() - start_time, 2)

        risk_score = 0
        risk_factors: List[str] = []
        critical_count = sum(1 for f in findings if f.severity.value == "CRITICAL")
        high_count = sum(1 for f in findings if f.severity.value == "HIGH")

        if critical_count > 0:
            risk_score = 95
            risk_factors.append(f"CRITICAL: Found {critical_count} critical credentials (AWS keys, Private keys, PATs).")
        elif high_count > 0:
            risk_score = 75
            risk_factors.append(f"HIGH: Found {high_count} high-severity credentials / API keys.")
        elif findings:
            risk_score = 40
            risk_factors.append(f"Found {len(findings)} low-to-medium entropy potential secrets.")

        report = IntelligenceReport(
            target=target_name,
            target_type=TargetType.SECRETS,
            execution_time_seconds=duration,
            summary={
                "total_secrets_found": len(findings),
                "critical": critical_count,
                "high": high_count,
            },
            secret_results=findings,
            risk_score=risk_score,
            risk_factors=risk_factors,
        )
        return report

    def scan_metadata(self, file_path: str) -> IntelligenceReport:
        start_time = time.monotonic()
        finding = self.metadata_hunter.scan_file(file_path)
        duration = round(time.monotonic() - start_time, 2)

        risk_score = 10
        risk_factors: List[str] = []
        if finding.latitude and finding.longitude:
            risk_score = 85
            risk_factors.append(
                f"STALKING RISK: Precise GPS coordinates extracted ({finding.latitude}, {finding.longitude})."
            )
        if finding.make or finding.model:
            risk_factors.append(f"Hardware fingerprinting: Captured on {finding.make} {finding.model}.")
        if finding.datetime_original:
            risk_factors.append(f"Temporal metadata: Exact capture timestamp recorded ({finding.datetime_original}).")

        report = IntelligenceReport(
            target=os.path.basename(file_path),
            target_type=TargetType.METADATA,
            execution_time_seconds=duration,
            summary={
                "has_exif": finding.has_exif,
                "has_gps": bool(finding.latitude and finding.longitude),
                "device": f"{finding.make or ''} {finding.model or ''}".strip() or "Unknown",
            },
            metadata_results=[finding],
            risk_score=risk_score,
            risk_factors=risk_factors,
        )
        return report

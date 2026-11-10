import os
import re
import json
import time
from typing import Optional, List, Dict, Any
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
    """Central OSINT & Intelligence Correlation Orchestrator (SpiderFoot-style engine)."""

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
        risk_score = min(len(found_accounts) * 7, 70)

        # Correlate profiles, real names, avatars, and cross-referenced handles
        discovered_names = list({r.name for r in found_accounts if r.name})
        discovered_avatars = list({r.avatar_url for r in found_accounts if r.avatar_url})
        discovered_locations = list({r.location for r in found_accounts if r.location})

        connected_handles = set()
        connected_links = set()
        for r in found_accounts:
            for h in r.extracted_handles:
                connected_handles.add(h)
            for link in r.extracted_links:
                connected_links.add(link)

        risk_factors: List[str] = []
        if len(found_accounts) > 4:
            risk_factors.append(
                f"High digital footprint: Discovered {len(found_accounts)} active public accounts matching target handle."
            )
        dev_accounts = [r for r in found_accounts if r.category == "developer"]
        if dev_accounts:
            risk_factors.append(
                f"Developer profile exposure ({len(dev_accounts)} platforms). Code repos & commit histories publicly exposed."
            )

        if discovered_names:
            risk_score += 10
            risk_factors.append(f"Real / Display Names identified: {', '.join(discovered_names[:3])}.")

        if discovered_locations:
            risk_score += 10
            risk_factors.append(f"Geographic location leaked in profile metadata: {', '.join(discovered_locations[:2])}.")

        if connected_handles:
            risk_score += 10
            risk_factors.append(
                f"Web of Identity: Discovered {len(connected_handles)} cross-referenced handles ({', '.join(list(connected_handles)[:4])})."
            )

        report = IntelligenceReport(
            target=username,
            target_type=TargetType.USERNAME,
            execution_time_seconds=duration,
            summary={
                "total_probed": len(results),
                "total_found": len(found_accounts),
                "platforms_found": [r.platform for r in found_accounts],
                "discovered_names": discovered_names,
                "discovered_locations": discovered_locations,
                "connected_handles": sorted(list(connected_handles)),
                "connected_links": sorted(list(connected_links)),
            },
            identity_results=results,
            risk_score=min(risk_score, 100),
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
                "location": finding.location,
            },
            phone_results=finding,
            risk_score=min(risk_score, 100),
            risk_factors=risk_factors,
        )
        return report

    async def scan_domain(self, domain: str) -> IntelligenceReport:
        start_time = time.monotonic()
        finding = await self.domain_hunter.scan(domain)
        duration = round(time.monotonic() - start_time, 2)

        risk_score = 15
        risk_factors: List[str] = []

        if finding.email_spoofable:
            risk_score += 40
            risk_factors.append(
                f"CRITICAL EMAIL SPOOFING: {finding.dmarc_grade}. Attackers can forge emails from @{domain}."
            )
        else:
            risk_factors.append(f"Email Security: Protected by strict DMARC ({finding.dmarc_grade}).")

        if finding.exposed_emails:
            risk_score += 20
            risk_factors.append(
                f"Exposed Corporate Emails: {len(finding.exposed_emails)} addresses harvested via PGP / DNS records."
            )

        if len(finding.cert_transparency_subdomains) > 5:
            risk_score += 15
            risk_factors.append(
                f"Attack Surface: {len(finding.cert_transparency_subdomains)} subdomains mapped via Certificate Transparency logs."
            )

        # Security Headers Audit
        missing_sec = [h for h, present in finding.security_headers.items() if not present]
        if missing_sec:
            risk_score += 10
            risk_factors.append(f"Missing HTTP Security Headers: {', '.join(missing_sec)}.")

        report = IntelligenceReport(
            target=domain,
            target_type=TargetType.DOMAIN,
            execution_time_seconds=duration,
            summary={
                "ips": finding.ip_addresses,
                "cloud_provider": finding.cloud_provider,
                "dmarc_grade": finding.dmarc_grade,
                "spoofable": finding.email_spoofable,
                "exposed_emails": finding.exposed_emails,
                "subdomains_count": len(finding.discovered_subdomains),
                "cert_transparency_count": len(finding.cert_transparency_subdomains),
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

    def export_report(self, report: IntelligenceReport, output_dir: str = "reports") -> Dict[str, str]:
        """Automatically saves intelligence audit report as JSON and Markdown files in output_dir."""
        os.makedirs(output_dir, exist_ok=True)
        safe_name = re.sub(r'[^a-zA-Z0-9_\-.]', '_', report.target).strip('_')
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        base_name = f"{report.target_type.value}_{safe_name}_{timestamp}"

        # 1. JSON Report
        json_path = os.path.join(output_dir, f"{base_name}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            f.write(report.model_dump_json(indent=2))

        # 2. Markdown Executive Summary
        md_path = os.path.join(output_dir, f"{base_name}.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(f"# 🛰️ OSINT Intelligence Audit: {report.target}\n\n")
            f.write(f"- **Target Type:** `{report.target_type.value}`\n")
            f.write(f"- **Audit Timestamp:** `{report.generated_at}`\n")
            f.write(f"- **Execution Time:** `{report.execution_time_seconds}s`\n")
            f.write(f"- **Exposure & Risk Score:** `{report.risk_score} / 100`\n\n")

            if report.risk_factors:
                f.write("### ⚠️ Identified Threat & Exposure Vectors\n")
                for factor in report.risk_factors:
                    f.write(f"- {factor}\n")
                f.write("\n")

            # Identity details
            if report.identity_results:
                found = [r for r in report.identity_results if r.exists]
                f.write(f"### 👤 Discovered Accounts ({len(found)} / {len(report.identity_results)})\n\n")
                f.write("| Platform | Category | Profile URL | Extracted Name / Bio |\n")
                f.write("|---|---|---|---|\n")
                for r in found:
                    bio_snippet = (r.bio or r.name or "-").replace("\n", " ")[:60]
                    f.write(f"| **{r.platform}** | {r.category} | [{r.url}]({r.url}) | {bio_snippet} |\n")
                f.write("\n")

                if report.summary.get("connected_handles"):
                    f.write("#### 🔗 Web of Identity (Cross-Referenced Handles)\n")
                    for h in report.summary["connected_handles"]:
                        f.write(f"- `{h}`\n")
                    f.write("\n")

            # Phone details
            if report.phone_results:
                p = report.phone_results
                f.write("### 📞 Carrier & Telephony Recon\n\n")
                f.write(f"- **E.164:** `{p.e164}`\n")
                f.write(f"- **Carrier:** `{p.carrier}`\n")
                f.write(f"- **Line Type:** `{p.line_type}`\n")
                f.write(f"- **Location:** `{p.location}` (`{p.region_code}`)\n")
                f.write(f"- **Timezone:** `{p.timezone}`\n\n")

            # Domain details
            if report.domain_results:
                d = report.domain_results
                f.write("### 🌐 Domain & Infrastructure Recon\n\n")
                f.write(f"- **Cloud / CDN Provider:** `{d.cloud_provider}`\n")
                f.write(f"- **DMARC Security Grade:** `{d.dmarc_grade}`\n")
                f.write(f"- **Email Spoofing Risk:** `{'VULNERABLE' if d.email_spoofable else 'PROTECTED'}`\n")
                f.write(f"- **A Records (IPv4):** `{', '.join(d.ip_addresses) or 'None'}`\n")
                f.write(f"- **MX Records:** `{', '.join(d.mx_records) or 'None'}`\n\n")

                if d.exposed_emails:
                    f.write(f"#### ✉️ Exposed Corporate Emails ({len(d.exposed_emails)})\n")
                    for email in d.exposed_emails:
                        f.write(f"- `{email}`\n")
                    f.write("\n")

                if d.cert_transparency_subdomains:
                    f.write(f"#### 📜 Certificate Transparency Subdomains ({len(d.cert_transparency_subdomains)})\n")
                    for sub in d.cert_transparency_subdomains[:25]:
                        f.write(f"- `{sub}`\n")
                    f.write("\n")

            # Secrets details
            if report.secret_results:
                f.write(f"### 🔑 Detected Leaked Secrets ({len(report.secret_results)})\n\n")
                for s in report.secret_results:
                    f.write(f"- **[{s.severity.value}]** {s.description} at `{s.file_path}:{s.line_number}` (Snippet: `{s.matched_snippet}`)\n")
                f.write("\n")

            # Metadata details
            if report.metadata_results:
                m = report.metadata_results[0]
                f.write("### 📷 EXIF Geolocation & Camera Hardware\n\n")
                f.write(f"- **Device:** `{m.make or 'Unknown'} {m.model or ''}`\n")
                f.write(f"- **Timestamp:** `{m.datetime_original or 'Unknown'}`\n")
                if m.latitude:
                    f.write(f"- **GPS Coordinates:** `{m.latitude}, {m.longitude}` ([Google Maps Link]({m.maps_link}))\n")
                f.write("\n")

        return {"json": json_path, "markdown": md_path}

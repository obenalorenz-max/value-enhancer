import asyncio
import os
import re
from typing import List, Optional, Dict, Any, Set
import dns.resolver
import dns.asyncresolver

# Sanitize NO_PROXY for httpx compatibility with IPv6 brackets
for var in ("no_proxy", "NO_PROXY"):
    if var in os.environ and "[::1]" in os.environ[var]:
        os.environ[var] = os.environ[var].replace(",[::1]", "").replace("[::1]", "")

import httpx
from ..models import DomainFinding


COMMON_SUBDOMAINS = [
    "www", "mail", "api", "dev", "admin", "portal",
    "staging", "vpn", "auth", "app", "corp", "remote",
    "test", "beta", "login", "internal", "secure", "dashboard",
    "gateway", "cloud", "sso", "support", "mx", "git"
]


class DomainHunter:
    """Enterprise domain infrastructure mapping, Certificate Transparency harvester,
    cloud provider fingerprinting, and email leak detector (theHarvester architecture)."""

    def __init__(self, timeout: float = 3.5):
        self.timeout = timeout
        self.resolver = dns.resolver.Resolver()
        self.resolver.lifetime = timeout
        self.async_resolver = dns.asyncresolver.Resolver()
        self.async_resolver.lifetime = timeout
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/html, */*",
        }

    def _resolve_record(self, domain: str, rtype: str) -> List[str]:
        try:
            answers = self.resolver.resolve(domain, rtype)
            return [str(r.to_text()).strip('"') for r in answers]
        except Exception:
            return []

    async def _probe_subdomain(self, fqdn: str) -> Optional[str]:
        try:
            answers = await self.async_resolver.resolve(fqdn, "A")
            if answers:
                return fqdn
        except Exception:
            pass
        return None

    async def _harvest_crtsh_subdomains(self, domain: str, client: httpx.AsyncClient) -> List[str]:
        """Harvest all issued SSL Certificate subdomains from crt.sh (Certificate Transparency logs)."""
        subdomains: Set[str] = set()
        url = f"https://crt.sh/?q=%.{domain}&output=json"
        try:
            resp = await client.get(url, headers=self.headers, timeout=5.0)
            if resp.status_code == 200:
                data = resp.json()
                for entry in data:
                    name_value = entry.get("name_value", "")
                    for item in name_value.split("\n"):
                        item = item.strip().lower()
                        if item.startswith("*."):
                            item = item[2:]
                        if item.endswith(domain) and item != domain:
                            subdomains.add(item)
        except Exception:
            pass
        return sorted(list(subdomains))

    async def _harvest_exposed_emails(self, domain: str, client: httpx.AsyncClient, txt_records: List[str]) -> List[str]:
        """Find exposed corporate emails via SOA, DNS records, and public PGP key directories."""
        emails: Set[str] = set()
        email_regex = re.compile(rf'[a-zA-Z0-9_.+-]+@{re.escape(domain)}', re.IGNORECASE)

        # 1. Check DNS TXT records
        for txt in txt_records:
            for match in email_regex.findall(txt):
                emails.add(match.lower())

        # 2. Check SOA hostmaster email
        try:
            soa_answers = self.resolver.resolve(domain, "SOA")
            for r in soa_answers:
                rname = str(r.rname).rstrip(".")
                if "." in rname:
                    first, rest = rname.split(".", 1)
                    hostmaster = f"{first}@{rest}"
                    if hostmaster.endswith(domain):
                        emails.add(hostmaster.lower())
        except Exception:
            pass

        # 3. Query public PGP keyserver directory (theHarvester method)
        try:
            pgp_url = f"https://keys.openpgp.org/vks/v1/by-email/{domain}"
            resp = await client.get(pgp_url, headers=self.headers, timeout=3.0)
            if resp.status_code == 200:
                for match in email_regex.findall(resp.text):
                    emails.add(match.lower())
        except Exception:
            pass

        return sorted(list(emails))

    async def _inspect_web_and_cloud(
        self, domain: str, ns_records: List[str], client: httpx.AsyncClient
    ) -> Dict[str, Any]:
        """Detect cloud provider, server banner, and security headers (HSTS, CSP, X-Frame-Options)."""
        cloud_provider = "Unknown / Bare Metal"
        server_banner = None
        security_headers: Dict[str, bool] = {
            "Strict-Transport-Security": False,
            "Content-Security-Policy": False,
            "X-Frame-Options": False,
            "X-Content-Type-Options": False,
        }

        # Check Nameservers for Cloud Providers
        ns_blob = " ".join(ns_records).lower()
        if "cloudflare.com" in ns_blob:
            cloud_provider = "Cloudflare"
        elif "awsdns" in ns_blob:
            cloud_provider = "Amazon Web Services (Route53)"
        elif "googledomains.com" in ns_blob or "googlecloud" in ns_blob:
            cloud_provider = "Google Cloud (GCP)"
        elif "azure-dns" in ns_blob:
            cloud_provider = "Microsoft Azure"

        # HTTP Header Analysis
        for proto in ("https://", "http://"):
            try:
                target_url = f"{proto}{domain}"
                resp = await client.get(target_url, headers=self.headers, timeout=4.0, follow_redirects=True)
                headers = resp.headers

                server_banner = headers.get("server")
                if "cloudflare" in (server_banner or "").lower() or "cf-ray" in headers:
                    cloud_provider = "Cloudflare Edge"
                elif "x-amz-cf-id" in headers or "cloudfront" in (server_banner or "").lower():
                    cloud_provider = "AWS CloudFront"
                elif "x-fastly-request-id" in headers:
                    cloud_provider = "Fastly CDN"
                elif "x-vercel-id" in headers:
                    cloud_provider = "Vercel Edge Network"

                for sec_header in security_headers.keys():
                    if sec_header.lower() in headers:
                        security_headers[sec_header] = True
                break
            except Exception:
                continue

        return {
            "cloud_provider": cloud_provider,
            "server_banner": server_banner,
            "security_headers": security_headers,
        }

    async def scan(self, domain: str, check_subdomains: bool = True) -> DomainFinding:
        clean_domain = (
            domain.lower().strip()
            .replace("http://", "")
            .replace("https://", "")
            .split("/")[0]
            .split(":")[0]
        )

        # 1. Base DNS records
        ip_addresses = self._resolve_record(clean_domain, "A")
        ipv6_addresses = self._resolve_record(clean_domain, "AAAA")
        mx_records = self._resolve_record(clean_domain, "MX")
        txt_records = self._resolve_record(clean_domain, "TXT")
        ns_records = self._resolve_record(clean_domain, "NS")

        # 2. SPF Record Detection
        spf_record = None
        for txt in txt_records:
            if txt.startswith("v=spf1"):
                spf_record = txt
                break

        # 3. DMARC Record Detection & Grading
        dmarc_record = None
        dmarc_domain = f"_dmarc.{clean_domain}"
        dmarc_txts = self._resolve_record(dmarc_domain, "TXT")
        for txt in dmarc_txts:
            if txt.startswith("v=DMARC1"):
                dmarc_record = txt
                break

        email_spoofable = False
        dmarc_grade = "Grade F (Unprotected)"
        if not dmarc_record:
            email_spoofable = True
            dmarc_grade = "Grade F (Missing DMARC - Phishing Risk)"
        elif "p=reject" in dmarc_record.lower():
            email_spoofable = False
            dmarc_grade = "Grade A+ (Strict Reject Enforcement)"
        elif "p=quarantine" in dmarc_record.lower():
            email_spoofable = False
            dmarc_grade = "Grade B (Quarantine Spam Routing)"
        elif "p=none" in dmarc_record.lower():
            email_spoofable = True
            dmarc_grade = "Grade F (Monitoring Only 'p=none' - Spoofable)"

        # 4. Asynchronous Harvester modules (crt.sh, HTTP inspection, PGP emails)
        async with httpx.AsyncClient(verify=False) as client:
            subdomain_tasks = []
            if check_subdomains:
                subdomain_tasks = [
                    self._probe_subdomain(f"{sub}.{clean_domain}")
                    for sub in COMMON_SUBDOMAINS
                ]

            crtsh_task = self._harvest_crtsh_subdomains(clean_domain, client)
            web_cloud_task = self._inspect_web_and_cloud(clean_domain, ns_records, client)
            emails_task = self._harvest_exposed_emails(clean_domain, client, txt_records)

            probe_results, crt_subs, web_cloud_info, exposed_emails = await asyncio.gather(
                asyncio.gather(*subdomain_tasks) if subdomain_tasks else asyncio.sleep(0, result=[]),
                crtsh_task,
                web_cloud_task,
                emails_task,
            )

        active_probed = [s for s in probe_results if s is not None]
        all_discovered = sorted(list(set(active_probed + crt_subs)))

        return DomainFinding(
            domain=clean_domain,
            ip_addresses=ip_addresses,
            ipv6_addresses=ipv6_addresses,
            mx_records=mx_records,
            txt_records=txt_records,
            name_servers=ns_records,
            spf_record=spf_record,
            dmarc_record=dmarc_record,
            email_spoofable=email_spoofable,
            dmarc_grade=dmarc_grade,
            cloud_provider=web_cloud_info.get("cloud_provider"),
            server_banner=web_cloud_info.get("server_banner"),
            security_headers=web_cloud_info.get("security_headers", {}),
            exposed_emails=exposed_emails,
            cert_transparency_subdomains=crt_subs[:30],
            discovered_subdomains=all_discovered[:50],
        )

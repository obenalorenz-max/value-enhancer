import asyncio
from typing import List, Optional
import dns.resolver
import dns.asyncresolver
from ..models import DomainFinding


COMMON_SUBDOMAINS = [
    "www", "mail", "api", "dev", "admin", "portal",
    "staging", "vpn", "auth", "app", "corp", "remote",
    "test", "beta", "login", "internal", "secure", "dashboard"
]


class DomainHunter:
    """Domain infrastructure, DNS mapping, and email spoofability analyzer (theHarvester style)."""

    def __init__(self, timeout: float = 3.0):
        self.resolver = dns.resolver.Resolver()
        self.resolver.lifetime = timeout
        self.async_resolver = dns.asyncresolver.Resolver()
        self.async_resolver.lifetime = timeout

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

    async def scan(self, domain: str, check_subdomains: bool = True) -> DomainFinding:
        clean_domain = domain.lower().strip().replace("http://", "").replace("https://", "").split("/")[0]

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

        # 3. DMARC Record Detection
        dmarc_record = None
        dmarc_domain = f"_dmarc.{clean_domain}"
        dmarc_txts = self._resolve_record(dmarc_domain, "TXT")
        for txt in dmarc_txts:
            if txt.startswith("v=DMARC1"):
                dmarc_record = txt
                break

        # 4. Email Spoofability Assessment
        email_spoofable = False
        if not dmarc_record:
            email_spoofable = True
        elif "p=none" in dmarc_record.lower():
            # Monitoring only, does not enforce rejection/quarantine
            email_spoofable = True

        # 5. Fast Asynchronous Subdomain Enumeration
        discovered_subs: List[str] = []
        if check_subdomains:
            tasks = [
                self._probe_subdomain(f"{sub}.{clean_domain}")
                for sub in COMMON_SUBDOMAINS
            ]
            results = await asyncio.gather(*tasks)
            discovered_subs = [s for s in results if s is not None]

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
            discovered_subdomains=discovered_subs,
        )

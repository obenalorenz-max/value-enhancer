import urllib.parse
from typing import Optional, List
import phonenumbers
from phonenumbers import geocoder, carrier, timezone
from ..models import PhoneFinding


class PhoneHunter:
    """Phone number intelligence and carrier reconnaissance engine (PhoneInfoga style)."""

    @staticmethod
    def _generate_dorks(raw_phone: str, e164: Optional[str]) -> List[str]:
        """Generate targeted OSINT search queries for digital footprinting."""
        dork_queries = [
            f'"{raw_phone}"',
            f'site:facebook.com "{raw_phone}"',
            f'site:instagram.com "{raw_phone}"',
            f'site:linkedin.com "{raw_phone}"',
            f'site:pastebin.com "{raw_phone}"',
        ]
        if e164 and e164 != raw_phone:
            dork_queries.extend([
                f'"{e164}"',
                f'site:t.me "{e164}"',
                f'site:whatsapp.com "{e164}"',
            ])

        links = [
            f"https://www.google.com/search?q={urllib.parse.quote(q)}"
            for q in dork_queries
        ]
        return links

    def scan(self, raw_input: str, default_region: str = "PH") -> PhoneFinding:
        clean_input = raw_input.strip()

        try:
            # Parse with optional default region fallback if no international prefix
            parsed = phonenumbers.parse(clean_input, default_region)
            is_valid = phonenumbers.is_valid_number(parsed)
            is_possible = phonenumbers.is_possible_number(parsed)

            e164 = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
            international = phonenumbers.format_number(
                parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL
            )
            national = phonenumbers.format_number(
                parsed, phonenumbers.PhoneNumberFormat.NATIONAL
            )

            country_code = parsed.country_code
            region = phonenumbers.region_code_for_number(parsed)

            # Extract location description
            geo_desc = geocoder.description_for_number(parsed, "en") or None

            # Extract carrier details
            carrier_name = carrier.name_for_number(parsed, "en") or None

            # Extract line type (Mobile, Fixed Line, VOIP, Toll-free, etc.)
            num_type = phonenumbers.number_type(parsed)
            type_mapping = {
                phonenumbers.PhoneNumberType.FIXED_LINE: "Fixed Line",
                phonenumbers.PhoneNumberType.MOBILE: "Mobile",
                phonenumbers.PhoneNumberType.FIXED_LINE_OR_MOBILE: "Fixed Line / Mobile",
                phonenumbers.PhoneNumberType.TOLL_FREE: "Toll Free",
                phonenumbers.PhoneNumberType.PREMIUM_RATE: "Premium Rate",
                phonenumbers.PhoneNumberType.SHARED_COST: "Shared Cost",
                phonenumbers.PhoneNumberType.VOIP: "VOIP (Virtual / Burner)",
                phonenumbers.PhoneNumberType.PERSONAL_NUMBER: "Personal Number",
                phonenumbers.PhoneNumberType.PAGER: "Pager",
                phonenumbers.PhoneNumberType.UAN: "Universal Access Number",
                phonenumbers.PhoneNumberType.VOICEMAIL: "Voicemail",
            }
            line_type = type_mapping.get(num_type, "Unknown")

            # Extract timezones
            tz_list = timezone.time_zones_for_number(parsed)
            tz_str = ", ".join(tz_list) if tz_list else None

            dorks = self._generate_dorks(clean_input, e164)

            return PhoneFinding(
                raw_input=clean_input,
                valid=is_valid,
                possible=is_possible,
                e164=e164,
                international=international,
                national=national,
                country_code=country_code,
                region_code=region,
                location=geo_desc,
                carrier=carrier_name,
                line_type=line_type,
                timezone=tz_str,
                google_dorks=dorks,
            )

        except Exception:
            return PhoneFinding(
                raw_input=clean_input,
                valid=False,
                possible=False,
                google_dorks=self._generate_dorks(clean_input, None),
            )

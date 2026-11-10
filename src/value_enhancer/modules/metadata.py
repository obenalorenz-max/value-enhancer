import os
from typing import Optional, Dict, Any, Tuple
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from ..models import MetadataFinding


def _convert_to_degrees(value) -> float:
    """Helper to convert GPS degree/minute/second tuples to decimal degrees."""
    try:
        d = float(value[0])
        m = float(value[1])
        s = float(value[2])
        return d + (m / 60.0) + (s / 3600.0)
    except Exception:
        return 0.0


class MetadataHunter:
    """Image EXIF and GPS geolocation metadata harvester."""

    def scan_file(self, file_path: str) -> MetadataFinding:
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        file_size = os.path.getsize(file_path)
        filename = os.path.basename(file_path)

        try:
            with Image.open(file_path) as img:
                exif_data = img._getexif()

            if not exif_data:
                return MetadataFinding(
                    filename=filename,
                    file_size_bytes=file_size,
                    has_exif=False,
                )

            parsed_tags: Dict[str, Any] = {}
            for tag_id, val in exif_data.items():
                tag_name = TAGS.get(tag_id, str(tag_id))
                parsed_tags[tag_name] = val

            make = str(parsed_tags.get("Make", "")).strip() or None
            model = str(parsed_tags.get("Model", "")).strip() or None
            software = str(parsed_tags.get("Software", "")).strip() or None
            datetime_orig = str(parsed_tags.get("DateTimeOriginal", "")).strip() or None

            # Parse GPS data
            latitude: Optional[float] = None
            longitude: Optional[float] = None
            altitude: Optional[float] = None
            maps_link: Optional[str] = None

            gps_info = parsed_tags.get("GPSInfo")
            if gps_info and isinstance(gps_info, dict):
                gps_tags: Dict[str, Any] = {}
                for k, v in gps_info.items():
                    sub_name = GPSTAGS.get(k, str(k))
                    gps_tags[sub_name] = v

                lat_raw = gps_tags.get("GPSLatitude")
                lat_ref = gps_tags.get("GPSLatitudeRef", "N")
                lon_raw = gps_tags.get("GPSLongitude")
                lon_ref = gps_tags.get("GPSLongitudeRef", "E")
                alt_raw = gps_tags.get("GPSAltitude")

                if lat_raw and lon_raw:
                    lat_val = _convert_to_degrees(lat_raw)
                    if lat_ref == "S":
                        lat_val = -lat_val

                    lon_val = _convert_to_degrees(lon_raw)
                    if lon_ref == "W":
                        lon_val = -lon_val

                    latitude = round(lat_val, 6)
                    longitude = round(lon_val, 6)
                    maps_link = f"https://www.google.com/maps?q={latitude},{longitude}"

                if alt_raw:
                    try:
                        altitude = round(float(alt_raw), 2)
                    except Exception:
                        pass

            raw_str_tags = {
                k: str(v)[:80] for k, v in parsed_tags.items() if k != "GPSInfo"
            }

            return MetadataFinding(
                filename=filename,
                file_size_bytes=file_size,
                has_exif=True,
                make=make,
                model=model,
                software=software,
                datetime_original=datetime_orig,
                latitude=latitude,
                longitude=longitude,
                altitude=altitude,
                maps_link=maps_link,
                raw_tags=raw_str_tags,
            )

        except Exception:
            return MetadataFinding(
                filename=filename,
                file_size_bytes=file_size,
                has_exif=False,
            )

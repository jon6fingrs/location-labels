#!/usr/bin/env python3
"""
Write each image's location (from its GPS coordinates) into the IPTC
"Caption/Abstract" field, so Kodi's Picture Slideshow screensaver can show it.

Coordinates are reverse geocoded with Nominatim. The public server is limited
to one request per second; a self-hosted server is used without a limit.
"""

import argparse
import json
import os
import subprocess
import sys
import time

import requests

OFFICIAL_NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"
IMAGE_EXTENSIONS = ("jpg", "jpeg", "png", "tif", "tiff", "heic", "heif")
USER_AGENT = "location-labels/2.0 (+https://github.com/jon6fingrs/location-labels)"


class Geocoder:
    def __init__(self, url, language, omit_countries, email=None):
        self.url = url or OFFICIAL_NOMINATIM_URL
        self.is_official = self.url == OFFICIAL_NOMINATIM_URL
        self.language = language
        self.omit_countries = {c.lower() for c in omit_countries}
        self.email = email
        self.session = requests.Session()
        self.session.headers["User-Agent"] = USER_AGENT
        self.cache = {}
        self.last_request = 0.0

    def lookup(self, lat, lon):
        # Photos taken a few metres apart share one lookup.
        key = (round(lat, 4), round(lon, 4))
        if key not in self.cache:
            self.cache[key] = self._request(lat, lon)
        return self.cache[key]

    def _request(self, lat, lon):
        if self.is_official:
            # Nominatim usage policy: at most one request per second.
            wait = 1.0 - (time.monotonic() - self.last_request)
            if wait > 0:
                time.sleep(wait)
        params = {"lat": lat, "lon": lon, "format": "jsonv2", "accept-language": self.language}
        if self.email:
            params["email"] = self.email
        try:
            response = self.session.get(self.url, params=params, timeout=30)
        finally:
            self.last_request = time.monotonic()
        response.raise_for_status()
        return self._format(response.json().get("address", {}))

    def _format(self, address):
        city = (
            address.get("city") or address.get("town") or address.get("village")
            or address.get("hamlet") or address.get("municipality") or address.get("county")
        )
        state = address.get("state") or address.get("state_district") or address.get("region")
        country = address.get("country")
        if country and country.lower() in self.omit_countries:
            country = None
        if (address.get("country_code") or "").lower() in self.omit_countries:
            country = None

        parts = []
        for part in (city, state, country):
            if part and part not in parts:
                parts.append(part)
        return ", ".join(parts) or None


def read_metadata(paths):
    """Read GPS coordinates and any existing caption for all images with one exiftool call."""
    command = [
        "exiftool", "-json", "-n", "-q", "-q", "-r",
        "-GPSLatitude", "-GPSLongitude", "-IPTC:Caption-Abstract", "-XMP-dc:Description",
    ]
    for ext in IMAGE_EXTENSIONS:
        command += ["-ext", ext]
    result = subprocess.run(command + list(paths), capture_output=True, text=True)
    if not result.stdout.strip():
        if result.returncode not in (0, 1):
            print(f"exiftool failed: {result.stderr.strip()}", file=sys.stderr)
        return []
    return json.loads(result.stdout)


def write_caption(image_path, caption):
    """Write the caption to IPTC Caption-Abstract (read by Kodi) and XMP Description."""
    command = [
        "exiftool", "-q", "-overwrite_original", "-charset", "iptc=UTF8",
        "-IPTC:CodedCharacterSet=UTF8", f"-IPTC:Caption-Abstract={caption}",
        f"-XMP-dc:Description={caption}", image_path,
    ]
    subprocess.run(command, check=True, capture_output=True, text=True)


def main():
    parser = argparse.ArgumentParser(description="Write image locations into the IPTC caption for Kodi.")
    parser.add_argument("paths", nargs="+", help="Images or directories (searched recursively)")
    parser.add_argument(
        "--nominatim-url", default=os.getenv("NOMINATIM_URL", ""),
        help="Reverse geocoding endpoint of a self-hosted Nominatim server, e.g. http://nominatim:8080/reverse "
             "(default: the public OpenStreetMap server, limited to 1 request/second)",
    )
    parser.add_argument("--language", default=os.getenv("NOMINATIM_LANGUAGE", "en"), help="Language for place names (default: en)")
    parser.add_argument(
        "--omit-country", action="append", default=None,
        help="Country name or code to leave out of captions; repeatable (default: us)",
    )
    parser.add_argument("--email", default=os.getenv("NOMINATIM_EMAIL"), help="Contact email sent to Nominatim (recommended for the public server)")
    parser.add_argument("--force", action="store_true", help="Rewrite images that already have a caption")
    args = parser.parse_args()

    for path in args.paths:
        if not os.path.exists(path):
            print(f"Warning: {path} does not exist. Skipping.")

    images = read_metadata([p for p in args.paths if os.path.exists(p)])
    if not images:
        print("No valid images found.")
        return 1

    omit = args.omit_country if args.omit_country is not None else ["us"]
    geocoder = Geocoder(args.nominatim_url, args.language, omit, args.email)
    written = skipped = failed = 0

    for meta in images:
        image_path = meta["SourceFile"]
        lat, lon = meta.get("GPSLatitude"), meta.get("GPSLongitude")
        if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)) or (lat == 0 and lon == 0):
            print(f"{image_path}: no GPS data. Skipping.")
            skipped += 1
            continue
        # HEIC files cannot hold IPTC, so their caption lives only in XMP.
        existing = meta.get("Caption-Abstract") or meta.get("Description")
        if existing and not args.force:
            print(f"{image_path}: already has caption \"{existing}\". Skipping.")
            skipped += 1
            continue

        try:
            location = geocoder.lookup(lat, lon)
            if not location:
                print(f"{image_path}: no place found for {lat:.5f}, {lon:.5f}. Skipping.")
                skipped += 1
                continue
            write_caption(image_path, location)
            print(f"{image_path}: {location}")
            written += 1
        except requests.RequestException as e:
            print(f"{image_path}: reverse geocoding failed: {e}", file=sys.stderr)
            failed += 1
        except subprocess.CalledProcessError as e:
            print(f"{image_path}: writing caption failed: {e.stderr.strip()}", file=sys.stderr)
            failed += 1

    print(f"Done: {written} captioned, {skipped} skipped, {failed} failed.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

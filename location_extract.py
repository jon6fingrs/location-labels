import piexif
import subprocess
from PIL import Image
import requests
import time

# Global variable for custom Nominatim server
#CUSTOM_NOMINATIM_SERVER = "http://10.0.0.111:8060/reverse"  # Define custom server URL or leave empty for the official server
CUSTOM_NOMINATIM_SERVER = ""

# Helper function to enforce rate limiting for the official server
def rate_limited_request(url, params, headers, rate_limit=1):
    """Perform a rate-limited request to comply with API usage policies."""
    time.sleep(1 / rate_limit)  # Enforce rate limit (1/sec by default)
    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()
    return response

def dms_to_decimal(degrees, minutes, seconds, direction):
    """Convert GPS coordinates from DMS format to decimal."""
    decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)
    if direction in ['S', 'W']:
        decimal = -decimal
    return decimal

def extract_gps(image_path):
    """Extract GPS coordinates from EXIF metadata using piexif."""
    img = Image.open(image_path)
    exif_data = piexif.load(img.info.get("exif", piexif.dump({})))
    
    gps_data = exif_data.get("GPS", {})
    if not gps_data:
        raise ValueError("No GPS data found in EXIF metadata.")

    try:
        latitude = gps_data[piexif.GPSIFD.GPSLatitude]
        latitude_ref = gps_data[piexif.GPSIFD.GPSLatitudeRef].decode("utf-8")
        longitude = gps_data[piexif.GPSIFD.GPSLongitude]
        longitude_ref = gps_data[piexif.GPSIFD.GPSLongitudeRef].decode("utf-8")

        lat_decimal = dms_to_decimal(*[x[0] / x[1] for x in latitude], latitude_ref)
        lon_decimal = dms_to_decimal(*[x[0] / x[1] for x in longitude], longitude_ref)

        return lat_decimal, lon_decimal
    except KeyError as e:
        raise ValueError(f"Missing GPS field: {e}")

def reverse_geocode(lat, lon):
    """Query the Nominatim API and format the location."""
    url = CUSTOM_NOMINATIM_SERVER or "https://nominatim.openstreetmap.org/reverse"
    params = {"lat": lat, "lon": lon, "format": "jsonv2"}
    headers = {"User-Agent": "MetadataUpdater/1.0"}  # Optional, identify your application

    # Use rate-limited request if using the official server
    if url == "https://nominatim.openstreetmap.org/reverse":
        response = rate_limited_request(url, params, headers)
    else:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
    data = response.json()

    # Extract address fields
    address = data.get("address", {})
    city = (
        address.get("city") or
        address.get("town") or
        address.get("village") or
        address.get("hamlet") or
        address.get("county") or
        "Unknown"
    )
    state = address.get("state") or address.get("state_district") or "Unknown"
    country = address.get("country", "Unknown")
    country_code = address.get("country_code", "").lower()

    # Build location parts dynamically
    parts = []
    if city != "Unknown":
        parts.append(city)
    if state != "Unknown":
        parts.append(state)
    if country != "Unknown" and country_code != "us":  # Include country only if not US
        parts.append(country)

    # Join parts into a single string
    return ", ".join(parts) if parts else "Unknown Location"

def write_iptc_caption_with_iptc(image_path, caption):
    """Write a caption to the IPTC 'Caption/Abstract' field using the `iptc` tool."""
    # Encode caption to UTF-8
    encoded_caption = caption.encode("utf-8").decode("utf-8")

    # Write the caption using iptc
    command = ["iptc", "-m", "Caption", "-v", encoded_caption, image_path]
    try:
        subprocess.run(command, check=True)
        print(f"Caption written to IPTC: {caption}")
    except subprocess.CalledProcessError as e:
        print(f"Error writing IPTC metadata: {e}")

def process_image(image_path):
    """Process a single image to extract GPS, reverse geocode, and write IPTC metadata."""
    try:
        # Step 1: Extract GPS coordinates
        print(f"Processing {image_path}...")
        lat, lon = extract_gps(image_path)
        print(f"GPS Coordinates: Latitude {lat}, Longitude {lon}")

        # Step 2: Reverse geocode to get the location name
        location = reverse_geocode(lat, lon)
        print(f"Resolved Location: {location}")

        # Step 3: Write location to IPTC caption
        write_iptc_caption_with_iptc(image_path, location)

    except ValueError as ve:
        print(f"Error processing {image_path}: {ve}")
    except Exception as e:
        print(f"Unexpected error processing {image_path}: {e}")

def main(inputs):
    """Main function to process images or directories."""
    import os
    images = []

    # Collect all image paths
    for input_path in inputs:
        if os.path.isfile(input_path):
            images.append(input_path)
        elif os.path.isdir(input_path):
            for root, _, files in os.walk(input_path):
                for file in files:
                    if file.lower().endswith(('.jpg', '.jpeg')):
                        images.append(os.path.join(root, file))
        else:
            print(f"Warning: {input_path} is not a valid file or directory. Skipping.")

    if not images:
        print("No valid images found.")
        return

    # Process each image
    for image_path in images:
        process_image(image_path)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 script.py <image_or_directory> [<image_or_directory> ...]")
        sys.exit(1)

    main(sys.argv[1:])

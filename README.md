
# Location Metadata Script for Images

This script processes images to extract GPS metadata, reverse geocode the coordinates to obtain a human-readable location, and embed the location as a caption in the image's metadata. It is particularly useful for enhancing the Kodi Picture Slideshow Screensaver by displaying the location of each image on the screen.

## Purpose

The primary purpose of this script is to:

1. Extract GPS coordinates from images using EXIF metadata.
2. Reverse geocode the coordinates to obtain a readable location (e.g., city, state, and country).
3. Embed the location into the image's IPTC "Caption/Abstract" field.

When used with the [Kodi Picture Slideshow Screensaver](https://kodi.wiki/view/Add-on:Picture_Slideshow_Screensaver), the embedded location metadata will display on-screen while the image is shown.

## Features

- Extracts GPS data from images in DMS format.
- Uses either a custom Nominatim server or the official Nominatim server for reverse geocoding.
- Complies with the official Nominatim server’s API rate limits (1 request per second).
- Writes the resolved location to the image’s metadata using the IPTC "Caption/Abstract" field.

## Prerequisites

1. Python 3.6 or later.
2. The following Python libraries:
   - `piexif`
   - `Pillow` (PIL)
   - `requests`
3. The `iptc` command-line tool must be installed on your system for writing metadata.
4. Install `iptc` on Ubuntu/Debian:
   ```bash
   sudo apt-get install iptcutils
   ```

## Installation

1. Clone or download this repository.
2. Install the required Python libraries:
   ```bash
   pip install piexif pillow requests pillow_heif
   ```

## Usage

1. **Edit the Script for Custom Nominatim Server**:
   - If you have a custom Nominatim server, set its URL in the `CUSTOM_NOMINATIM_SERVER` variable at the top of the script.
   - Leave it empty (`""`) to use the official Nominatim server.

2. **Run the Script**:
   Use the script with images or directories containing images.
   ```bash
   python3 script.py <image_or_directory> [<image_or_directory> ...]
   ```
   Examples:
   - Process a single image:
     ```bash
     python3 script.py example.jpg
     ```
   - Process all images in a directory:
     ```bash
     python3 script.py /path/to/image_directory
     ```

3. **Output**:
   - The script processes each image, extracts GPS coordinates, resolves the location, and writes it to the IPTC metadata field "Caption/Abstract."
   - If an image has no GPS data or an error occurs, a warning will be displayed.

## How It Works

1. **GPS Extraction**: The script reads EXIF metadata to extract GPS coordinates in Degrees, Minutes, Seconds (DMS) format.
2. **Reverse Geocoding**: Coordinates are sent to a Nominatim API to resolve a human-readable location.
3. **Write Metadata**: The resolved location is written back into the image's IPTC "Caption/Abstract" field using the `iptc` command-line tool.

## Notes

- **API Rate Limits**: When using the official Nominatim server, the script enforces a rate limit of 1 request per second to comply with usage policies.
- **Custom Nominatim Server**: If you self-host a Nominatim server, ensure it is accessible and correctly configured.
- **File Types**: The script processes only `.jpg, .jpeg, .png, .tiff, .heic, and .heif` files.

## Troubleshooting

1. **Missing Dependencies**:
   - Ensure the required Python libraries are installed.
   - Ensure the `iptc` command-line tool is installed and available in your system's PATH.
2. **No GPS Data**:
   - Some images may not contain GPS metadata. The script will skip these files with a warning.
3. **Permission Errors**:
   - Ensure you have write permissions for the images you are processing.

## License

This script is licensed under the MIT License. Feel free to modify and use it for your projects.

---

Enhance your Kodi Picture Slideshow experience with dynamic location metadata for your images!


# Location Metadata Script for Images

This script reads the GPS coordinates of your images, looks up a readable place name (e.g. "Boston, Massachusetts" or "Kyoto, Kyoto Prefecture, Japan") and writes it into the image's IPTC "Caption/Abstract" field. With the [Kodi Picture Slideshow Screensaver](https://kodi.wiki/view/Add-on:Picture_Slideshow_Screensaver), the location is then shown on screen with each photo.

> **Using [immich-dl](https://github.com/jon6fingrs/immich-dl)?** It can now write these captions itself (`WRITE_LOCATION_CAPTION=true`), using the locations Immich has already looked up. No Nominatim server and no second step needed. This script is still useful for images that don't come from Immich.

## Features

- Reads GPS data from JPEG, PNG, TIFF and HEIC/HEIF files with exiftool.
- Reverse geocodes with the public OpenStreetMap Nominatim server or your own self-hosted one.
- Follows the public server's usage policy (at most 1 request per second, identifying User-Agent). A self-hosted server is used at full speed.
- Caches lookups, so photos taken in the same spot cost one request.
- Skips images that already have a caption, so it's cheap to run again on the same folder (use `--force` to rewrite them).
- Leaves the country out for your home country (US by default).

## Prerequisites

1. Python 3.8 or later.
2. [exiftool](https://exiftool.org/):
   ```bash
   sudo apt-get install libimage-exiftool-perl
   ```
3. The Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

```bash
python3 location_extract.py <image_or_directory> [<image_or_directory> ...] [options]
```

Directories are searched recursively.

Examples:

```bash
# Using the public Nominatim server
python3 location_extract.py /path/to/screensaver --email you@example.com

# Using a self-hosted Nominatim server
python3 location_extract.py /path/to/screensaver --nominatim-url http://nominatim.local:8080/reverse

# Rewrite every caption, leaving out the country for photos taken in Canada
python3 location_extract.py /path/to/screensaver --force --omit-country ca
```

### Options

| Option | Environment Variable | Description |
|---|---|---|
| `--nominatim-url URL` | `NOMINATIM_URL` | Reverse geocoding endpoint of a self-hosted Nominatim server, ending in `/reverse`. Default: the public OpenStreetMap server. |
| `--language LANG` | `NOMINATIM_LANGUAGE` | Language for place names. Default `en`. |
| `--omit-country NAME_OR_CODE` | | Leave this country out of captions. Repeatable. Default `us`. |
| `--email ADDRESS` | `NOMINATIM_EMAIL` | Contact address sent to Nominatim. Recommended when using the public server. |
| `--force` | | Rewrite images that already have a caption. |

The script exits with a non-zero code if any lookup or write failed.

### Running after immich-dl

To caption each new selection, run the script right after the downloader in the same cron job:

```cron
0 3 * * * cd /path/to/immich-dl && python3 immich-dl.py && python3 /path/to/location-labels/location_extract.py /path/to/screensaver
```

## How It Works

1. **GPS extraction**: exiftool reads the GPS latitude and longitude of every image in one pass.
2. **Reverse geocoding**: the coordinates are sent to Nominatim, which returns the city, state and country.
3. **Writing metadata**: the place name is written to the IPTC "Caption/Abstract" field (shown by Kodi) and the XMP description. HEIC files can't hold IPTC data, so they only get the XMP description.

## Troubleshooting

1. **"exiftool failed" or no images found**: make sure exiftool is installed and on your `PATH`.
2. **No GPS data**: some images don't have location metadata. They are skipped.
3. **HTTP 403 or 429 from the public server**: you're being rate limited or blocked. Pass `--email`, or self-host Nominatim for large libraries.
4. **Permission errors**: make sure you can write to the images.

## License

This script is licensed under the MIT License. Feel free to modify and use it for your projects.

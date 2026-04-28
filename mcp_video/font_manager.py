"""Font management — download Google Fonts for use in video overlays."""

from __future__ import annotations

import os
import urllib.request
import urllib.error

from .errors import MCPVideoError

_FONT_CACHE_DIR = os.path.expanduser("~/.cache/mcp-video/fonts")

# Map of common Google Fonts names to their direct TTF URLs
_GOOGLE_FONT_URLS: dict[str, str] = {
    "roboto": "https://github.com/google/fonts/raw/main/apache/roboto/Roboto%5Bwdth,wght%5D.ttf",
    "opensans": "https://github.com/google/fonts/raw/main/ofl/opensans/OpenSans%5Bwdth,wght%5D.ttf",
    "lato": "https://github.com/google/fonts/raw/main/ofl/lato/Lato-Regular.ttf",
    "montserrat": "https://github.com/google/fonts/raw/main/ofl/montserrat/Montserrat%5Bwght%5D.ttf",
    "poppins": "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Regular.ttf",
    "inter": "https://github.com/google/fonts/raw/main/ofl/inter/Inter%5Bslnt,wght%5D.ttf",
    "oswald": "https://github.com/google/fonts/raw/main/ofl/oswald/Oswald%5Bwght%5D.ttf",
    "raleway": "https://github.com/google/fonts/raw/main/ofl/raleway/Raleway%5Bwght%5D.ttf",
    "ubuntu": "https://github.com/google/fonts/raw/main/ofl/ubuntu/Ubuntu-Regular.ttf",
    "merriweather": "https://github.com/google/fonts/raw/main/ofl/merriweather/Merriweather%5Bwght%5D.ttf",
}


def resolve_font(font_name: str) -> str:
    """Return a local path to a font, downloading from Google Fonts if needed.

    Args:
        font_name: Font family name (e.g. "Roboto", "Open Sans").

    Returns:
        Absolute path to the local TTF file.

    Raises:
        MCPVideoError: If the font cannot be downloaded or found.
    """
    normalized = font_name.lower().replace(" ", "").replace("-", "")

    # Already a local file path?
    if os.path.isfile(font_name):
        return os.path.abspath(font_name)

    url = _GOOGLE_FONT_URLS.get(normalized)
    if url is None:
        raise MCPVideoError(
            f"Unknown font: '{font_name}'. Available: {list(_GOOGLE_FONT_URLS.keys())}",
            error_type="validation_error",
            code="unknown_font",
        )

    os.makedirs(_FONT_CACHE_DIR, exist_ok=True)
    local_path = os.path.join(_FONT_CACHE_DIR, f"{normalized}.ttf")

    if os.path.isfile(local_path):
        return local_path

    try:
        urllib.request.urlretrieve(url, local_path)
    except urllib.error.URLError as exc:
        raise MCPVideoError(
            f"Failed to download font '{font_name}': {exc}",
            error_type="processing_error",
            code="font_download_failed",
        ) from exc

    return local_path


def list_available_fonts() -> list[str]:
    """Return the list of built-in downloadable font names."""
    return list(_GOOGLE_FONT_URLS.keys())

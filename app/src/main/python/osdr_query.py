"""
Minimal NASA OSDR BDAPI v2 client using only the Python standard library
(httpx is not available on Chaquopy). Returns raw text; the app needs internet.

API: https://visualization.osdr.nasa.gov/biodata/api/v2
"""

import json
import urllib.parse
import urllib.request

BASE = "https://visualization.osdr.nasa.gov/biodata/api/v2"
TIMEOUT = 30


def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "ASTRA-BIO-Android/1.0"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.read().decode("utf-8", errors="replace")


def dataset_metadata(accession):
    """Full metadata tree for one dataset, e.g. 'OSD-48'."""
    acc = accession.strip().upper()
    return _get(f"{BASE}/dataset/{acc}/")


def dataset_files(accession):
    """File records (includes download URLs) as JSON text."""
    acc = accession.strip().upper()
    return _get(f"{BASE}/dataset/{acc}/files/")


def search_samples(organism=""):
    """Sample metadata via the query interface; returns CSV text."""
    params = {"study.factor value.spaceflight": ""}
    if organism:
        params["study.characteristics.organism"] = organism
    qs = "&".join(
        f"{urllib.parse.quote(k)}={urllib.parse.quote(v)}" for k, v in params.items()
        if v
    ) + ("&" if any(v for v in params.values()) else "") +         "&".join(urllib.parse.quote(k) for k, v in params.items() if not v)
    return _get(f"{BASE}/query/metadata/?{qs}")

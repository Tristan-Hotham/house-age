"""Shared paths, constants and helpers for the house-age study ("How old is your neighbourhood?").

Inputs (read in place, never modified):
  VOA/CTSOP4.1.zip  Valuation Office Agency (2025) Council Tax: stock of properties, 2025, table CTSOP4.1: properties by
                    Council Tax band and build period, England and Wales, by nation, region, county, local authority,
                    MSOA 2021 and LSOA 2021, at 31 March 2025. Official Statistics, Open Government Licence v3.0.
  VOA/CTSOP3.1.zip  Same release, table CTSOP3.1: properties by band, property type and number of bedrooms.
  LSOA_GPKG         ONS LSOA 2021 boundaries (generalised clipped, BGC), Open Government Licence v3.0, from the GitHub
                    copy drkane/geo-lookups (commit e20a072d5fc0918437abaa3622be63f40b71d9dd), merged by 00_boundaries.py.
  GEO/msoa21_bsc.geojson, lad23_bgc.geojson   ONS MSOA 2021 and LAD 2023 boundaries (OGL v3.0).
  GEO/ne_10m_populated_places_simple.geojson  Natural Earth populated places (public domain): the list of cities.
  SETTLE            Wikidata UK settlements (CC0): precise city-centre coordinates.
"""
import json, gzip, os, re, math

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CODE = os.path.join(ROOT, "code")
VOA = os.environ.get("HA_VOA", "/home/claude/newdata/raw_new14/houseage")
GEO = os.environ.get("HA_GEO", "/home/claude/newdata/raw/geo")
SETTLE = os.environ.get("HA_SETTLE", "/home/claude/newdata/raw_new8/uk_settlements.tsv")
FONTS = os.environ.get("HA_FONTS", "/home/claude/ref/fonts")
SCR = os.environ.get("HA_SCRATCH", "/home/claude/scratch/house-age")
LSOA_GPKG = os.path.join(SCR, "lsoa21_bgc.gpkg")
GEOLOOKUPS = "https://raw.githubusercontent.com/drkane/geo-lookups/e20a072d5fc0918437abaa3622be63f40b71d9dd/"
DATA = os.path.join(ROOT, "data")
IMG = os.path.join(ROOT, "img")
REL = os.path.join(ROOT, "release")
for d in (DATA, IMG, SCR):
    os.makedirs(d, exist_ok=True)

SLUG = "house-age"
TITLE = "How old is your neighbourhood?"
PAGE = f"https://maps.tristanhotham.com/{SLUG}/"
REPO = f"https://github.com/Tristan-Hotham/{SLUG}"
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")
BYLINE = "Dr Tristan Hotham · Independent researcher · 2026"

# build periods as published (VOA age codes); 2009 to 2025 are single years
PCOLS = ["bp_pre_1900", "bp_1900_1918", "bp_1919_1929", "bp_1930_1939", "bp_1945_1954", "bp_1955_1964", "bp_1965_1972",
         "bp_1973_1982", "bp_1983_1992", "bp_1993_1999", "bp_2000_2008"]
YCOLS = [f"bp_{y}" for y in range(2009, 2026)]
# the 12 map periods (2009 onwards combined)
PER = ["pre1900", "1900_1918", "1919_1929", "1930_1939", "1945_1954", "1955_1964", "1965_1972", "1973_1982",
       "1983_1992", "1993_1999", "2000_2008", "2009on"]
PER_LABEL = ["Before 1900", "1900 to 1918", "1919 to 1929", "1930 to 1939", "1945 to 1954", "1955 to 1964",
             "1965 to 1972", "1973 to 1982", "1983 to 1992", "1993 to 1999", "2000 to 2008", "2009 onwards"]
PER_SHORT = ["pre-1900", "1900-18", "1919-29", "1930-39", "1945-54", "1955-64", "1965-72", "1973-82", "1983-92",
             "1993-99", "2000-08", "2009+"]
MID = {"pre1900": 1875, "1900_1918": 1909, "1919_1929": 1924, "1930_1939": 1934.5, "1945_1954": 1949.5,
       "1955_1964": 1959.5, "1965_1972": 1968.5, "1973_1982": 1977.5, "1983_1992": 1987.5, "1993_1999": 1996,
       "2000_2008": 2004}
GROUPS = {"pre1919": ["pre1900", "1900_1918"], "interwar": ["1919_1929", "1930_1939"],
          "postwar": ["1945_1954", "1955_1964", "1965_1972"], "late20": ["1973_1982", "1983_1992", "1993_1999"],
          "early21": ["2000_2008"], "new": ["2009on"]}
GROUP_LABEL = {"pre1919": "Before 1919", "interwar": "Between the wars (1919 to 1939)", "postwar": "Post-war (1945 to 1972)",
               "late20": "1973 to 1999", "early21": "2000 to 2008", "new": "2009 onwards"}
# colours for the 12 periods: deep brown (oldest) through ochre and teal to deep blue (newest)
PCOL = ["#5B2A1A", "#8A3B22", "#B4562E", "#D27D3E", "#E3A65A", "#EDCB86", "#D9DDB0", "#A9D0C0", "#73B5B5", "#4691A8",
        "#2B6C95", "#1F3F78"]
REGIONS = {"E12000001": "North East", "E12000002": "North West", "E12000003": "Yorkshire and the Humber",
           "E12000004": "East Midlands", "E12000005": "West Midlands", "E12000006": "East of England",
           "E12000007": "London", "E12000008": "South East", "E12000009": "South West", "W92000004": "Wales"}
CATCH_KM = 20.0


def jload(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def nonan(v):
    if isinstance(v, float) and (v != v or v in (float("inf"), float("-inf"))):
        return None
    if isinstance(v, (list, tuple)):
        return [nonan(x) for x in v]
    if isinstance(v, dict):
        return {str(k): nonan(x) for k, x in v.items()}
    if hasattr(v, "item"):
        return nonan(v.item())
    return v


def jsave(obj, path, indent=None):
    obj = nonan(obj)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, allow_nan=False, indent=indent, separators=None if indent else (",", ":"))


def get(R, path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f=None):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(float(v)):,}"
    if f == "pc": return f"{round(float(v))}%"
    if f == "pc1": return f"{float(v):.1f}%"
    if f == "f0": return f"{float(v):.0f}"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    if f == "f3": return f"{float(v):.3f}"
    if f == "m1": return f"{float(v) / 1e6:.1f}"
    if f == "pc_frac": return (f"{float(v) * 100:.1f}%" if abs(float(v) * 100 - round(float(v) * 100)) > 0.05 else f"{round(float(v) * 100)}%")
    if f == "abs0": return f"{abs(float(v)):.0f}"
    if f == "abs1": return f"{abs(float(v)):.1f}"
    raise ValueError(f)


_T = None


def bng():
    global _T
    if _T is None:
        from pyproj import Transformer
        _T = (Transformer.from_crs(4326, 27700, always_xy=True), Transformer.from_crs(27700, 4326, always_xy=True))
    return _T


def read_voa(table, dash=0.0):
    """Read a CTSOP CSV from its zip. '-' (fewer than five properties) becomes `dash`."""
    import zipfile, pandas as pd
    z = zipfile.ZipFile(os.path.join(VOA, f"{table}.zip"))
    name = [n for n in z.namelist() if n.endswith(".csv")][0]
    d = pd.read_csv(z.open(name), dtype=str, encoding="utf-8-sig")
    num = d.columns[5:]
    for c in num:
        d[c] = d[c].replace("-", str(dash)).astype(float)
    return d


def period_counts(d):
    """Add the 12 map periods (2009 onwards combined) to a CTSOP4.1 frame."""
    out = d.copy()
    for k, c in zip(PER[:11], PCOLS):
        out[k] = d[c]
    out["2009on"] = d[YCOLS].sum(axis=1)
    out["unknown"] = d["bp_unkw"]
    out["known"] = out[PER].sum(axis=1)
    return out

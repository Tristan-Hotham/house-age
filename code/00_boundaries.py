"""Step 0: LSOA 2021 boundaries (ONS, generalised clipped, OGL v3.0) from the GitHub copy drkane/geo-lookups.
Downloads the nine English region files (boundaries/lsoa/E12*.geojson) and the 22 Welsh local authority files (W06*),
merges them, drops duplicates and writes SCR/lsoa21_bgc.gpkg. Skips if the file exists."""
import subprocess, urllib.request
import pandas as pd, geopandas as gpd
from common import *

if os.path.exists(LSOA_GPKG):
    print("exists", LSOA_GPKG); raise SystemExit
tmp = os.path.join(SCR, "lsoa_raw"); os.makedirs(tmp, exist_ok=True)
codes = [f"E1200000{i}" for i in range(1, 10)] + [f"W060000{i:02d}" for i in range(1, 25)]
parts = []
for c in codes:
    fn = os.path.join(tmp, c + ".geojson")
    try:
        urllib.request.urlretrieve(GEOLOOKUPS + f"boundaries/lsoa/{c}.geojson", fn)
    except Exception as e:
        print("missing", c, e); continue
    parts.append(gpd.read_file(fn)[["LSOA21CD", "LSOA21NM", "LADCD_ACTIVE", "RGNCD", "geometry"]])
g = pd.concat(parts).drop_duplicates("LSOA21CD")
assert len(g) == 35672, len(g)
g.to_file(LSOA_GPKG)
subprocess.run(["rm", "-rf", tmp])
print(len(g), "LSOAs")

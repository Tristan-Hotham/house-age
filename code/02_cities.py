"""Step 2: the list of cities and their centres. Cities = Natural Earth populated places in England and Wales with
pop_max >= 100,000 (public domain). Centre = the coordinate of the Wikidata item for that city (CC0; the item with the
matching name and the largest population within 15 km of the Natural Earth point; Natural Earth's point where no item
matches, which is Bradford only), Natural Earth's own point kept as a
sensitivity check (R4). Writes data/cities.csv."""
import numpy as np, pandas as pd, geopandas as gpd
from common import *

NAMEFIX = {"Newcastle": "Newcastle upon Tyne", "Stoke": "Stoke-on-Trent", "Brighton": "Brighton"}
ne = gpd.read_file(os.path.join(GEO, "ne_10m_populated_places_simple.geojson"))
ne = ne[(ne.adm0name == "United Kingdom") & (ne.pop_max >= 100000)]
lad = gpd.read_file(os.path.join(GEO, "lad23_bgc.geojson")).to_crs(4326)
ew = lad[lad.geometry.notna() & lad.iloc[:, 0].astype(str).str[0].isin(["E", "W"])] if False else lad
codecol = [c for c in lad.columns if c.upper().startswith("LAD") and c.upper().endswith("CD")][0]
ew = lad[lad[codecol].str[0].isin(["E", "W"])]
ne = gpd.sjoin(ne, ew[[codecol, "geometry"]], predicate="within", how="inner")
w = pd.read_csv(SETTLE, sep="\t")
w["name"] = w["?pl"].str.extract(r'^"?(.*?)"?@en$')[0]
w["pop"] = pd.to_numeric(w["?pop"].astype(str).str.extract(r"([0-9.]+)")[0], errors="coerce")
xy = w["?coord"].str.extract(r"POINT\(([-0-9.]+) ([-0-9.]+)\)").astype(float)
w["lon"], w["lat"] = xy[0], xy[1]
fwd, inv = bng()
rows = []
for r in ne.sort_values("pop_max", ascending=False).itertuples():
    nm = NAMEFIX.get(r.name, r.name)
    c = w[(w.name == nm)].copy()
    c["km"] = [math.dist(fwd.transform(lo, la), fwd.transform(r.longitude, r.latitude)) / 1000 for lo, la in zip(c.lon, c.lat)]
    c = c[c.km < 15].sort_values("pop", ascending=False)
    if len(c):
        b = c.iloc[0]
    else:   # no Wikidata item of that name in the file (Bradford): fall back to the Natural Earth point
        b = pd.Series({"lon": r.longitude, "lat": r.latitude, "?p": "<none>"})
    x, y = fwd.transform(b.lon, b.lat); xn, yn = fwd.transform(r.longitude, r.latitude)
    rows.append({"city": nm, "ne_pop_max": int(r.pop_max), "lon": round(b.lon, 5), "lat": round(b.lat, 5),
                 "wikidata": b["?p"].strip("<>").rsplit("/", 1)[-1], "x": round(x), "y": round(y),
                 "ne_lon": round(r.longitude, 5), "ne_lat": round(r.latitude, 5), "ne_x": round(xn), "ne_y": round(yn),
                 "ne_offset_km": round(math.dist((x, y), (xn, yn)) / 1000, 2)})
C = pd.DataFrame(rows)
C.to_csv(os.path.join(DATA, "cities.csv"), index=False)
print(C[["city", "wikidata", "lon", "lat", "ne_offset_km"]].to_string())

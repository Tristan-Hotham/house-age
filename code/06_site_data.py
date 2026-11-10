"""Step 6: page data. data/lsoa.topo.json (LSOA 2021 polygons simplified with mapshaper to 15% of vertices, weighted,
keeping every shape; features in the order of data/site_lsoa.json), data/site_lsoa.json (per LSOA: code, name, local
authority, homes, unknown share, share of known homes in each of the 12 periods, median period, mean year, nearest city
and distance), data/site.json (cities, local authorities and places for search, headline numbers)."""
import subprocess
import numpy as np, pandas as pd, geopandas as gpd
from common import *

X = pd.read_csv(f"{DATA}/lsoa_measures.csv", index_col="lsoa21cd")
R = jload(f"{DATA}/results.json")
CT = pd.read_csv(f"{DATA}/cities.csv")
P = pd.read_parquet(os.path.join(SCR, "lsoa_points.parquet"))
tmp = os.path.join(SCR, "lsoa_wgs.geojson")
g = gpd.read_file(LSOA_GPKG)[["LSOA21CD", "geometry"]]
g.to_file(tmp, driver="GeoJSON", COORDINATE_PRECISION=5)
subprocess.run(["mapshaper", tmp, "-simplify", "15%", "weighted", "keep-shapes", "-o", "format=topojson", "quantization=100000",
                os.path.join(SCR, "lsoa_topo_ids.json")], check=True)
T = jload(os.path.join(SCR, "lsoa_topo_ids.json"))
obj = list(T["objects"].values())[0]
codes = [geo["properties"]["LSOA21CD"] for geo in obj["geometries"]]
for geo in obj["geometries"]:
    geo.pop("properties", None)
T["objects"] = {"lsoa": obj}
jsave(T, f"{DATA}/lsoa.topo.json")
os.remove(tmp); os.remove(os.path.join(SCR, "lsoa_topo_ids.json"))
X = X.reindex(codes)
assert X.index.is_unique and X.name.notna().all()
lads = sorted(X.lad_name.unique())
li = {n: i for i, n in enumerate(lads)}
cities = list(CT.city)
pc = X[[f"pc_{p}" for p in PER]].to_numpy()
S = {"codes": codes, "names": X.name.tolist(), "lad": [li[n] for n in X.lad_name], "lads": lads,
     "n": X.homes.astype(int).tolist(), "u": np.round(X.unknown_share.to_numpy(), 1).tolist(),
     "p": np.round(pc).astype(int).tolist(), "m": X.median_period.map({l: k for k, l in enumerate(PER_LABEL)}).astype(int).tolist(),
     "y": np.round(X.mean_year.to_numpy()).astype(int).tolist(),
     "c": [cities.index(c) if isinstance(c, str) and c else -1 for c in X.city], "d": np.round(np.nan_to_num(X.km_to_centre.to_numpy(), nan=-1), 1).tolist()}
jsave(S, f"{DATA}/site_lsoa.json")
# local authorities: centre and bounds from the LSOA points
fwd, inv = bng()
P = P.reindex(codes)
lo, la = inv.transform(P.x.to_numpy(), P.y.to_numpy())
X["lo"], X["la"] = lo, la
LA = pd.read_csv(f"{DATA}/la_rank.csv", index_col="code")
las = []
for n, t in X.groupby("lad_name"):
    r = LA[LA.name == n]
    las.append({"n": n, "b": [round(t.lo.min(), 3), round(t.la.min(), 3), round(t.lo.max(), 3), round(t.la.max(), 3)],
                "pre": round(float(r.pre1919.iloc[0]), 1) if len(r) else None, "new": round(float(r.new.iloc[0]), 1) if len(r) else None,
                "med": r.median_period.iloc[0] if len(r) else None})
# places for search: Wikidata settlements (CC0) inside England and Wales, population at least 1,500
w = pd.read_csv(SETTLE, sep="\t")
w["name"] = w["?pl"].str.extract(r'^"?(.*?)"?@en$')[0]
w["pop"] = pd.to_numeric(w["?pop"].astype(str).str.extract(r"([0-9.]+)")[0], errors="coerce")
xy = w["?coord"].str.extract(r"POINT\(([-0-9.]+) ([-0-9.]+)\)").astype(float)
w["lon"], w["lat"] = xy[0], xy[1]
w = w[(w["pop"] >= 1500) & w.lon.notna() & ~w["?typel"].astype(str).str.contains("metropolitan|conurbation|urban area|built-up|region|county|agglomeration", case=False)]
w = w.sort_values("pop", ascending=False).drop_duplicates("name")
pts = gpd.GeoDataFrame(w, geometry=gpd.points_from_xy(w.lon, w.lat), crs=4326)
gg = gpd.read_file(LSOA_GPKG)[["LSOA21CD", "geometry"]]
pts = gpd.sjoin(pts, gg, predicate="within", how="inner")
places = [{"n": r.name, "lo": round(r.lon, 4), "la": round(r.lat, 4)} for r in pts.itertuples()]
site = {"cities": [{"n": r.city, "lo": r.lon, "la": r.lat} for r in CT.itertuples()],
        "las": las, "places": places, "per": PER_LABEL, "short": PER_SHORT, "col": PCOL,
        "groups": [{"k": g, "label": GROUP_LABEL[g], "idx": [PER.index(p) for p in ps]} for g, ps in GROUPS.items()],
        "nat": {p: round(R["nat"]["England and Wales"][p], 1) for p in PER}, "catch": CATCH_KM}
jsave(site, f"{DATA}/site.json")
for fn in ("lsoa.topo.json", "site_lsoa.json", "site.json"):
    print(fn, os.path.getsize(f"{DATA}/{fn}") // 1024, "KB")
print(len(places), "places", len(las), "local authorities")

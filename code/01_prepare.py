"""Step 1: tidy the VOA tables. Writes data/lsoa_age.csv (LSOA 2021: homes by build period, unknown, Council Tax band and
property type), data/msoa_age.csv, data/la_age.csv (local authorities), data/nation_band_period.csv (band x period for
England and Wales) and SCR/lsoa_points.parquet (representative points in BNG, LAD and region codes).
Set HA_DASH=2.5 to count suppressed cells ('-', fewer than five) as 2.5 instead of 0 (robustness R1)."""
import numpy as np, pandas as pd, geopandas as gpd
from common import *

DASH = float(os.environ.get("HA_DASH", "0"))
SUF = "" if DASH == 0 else f"_dash{DASH:g}"
d4 = period_counts(read_voa("CTSOP4.1", DASH))
d3 = read_voa("CTSOP3.1", DASH)
BANDS = list("ABCDEFGHI")


def build(level):
    a = d4[d4.geography == level]
    allb = a[a.band == "All"].set_index("ecode")
    out = allb[["area_name"] + PER + YCOLS + ["unknown", "known", "all_properties"]].copy()
    out.columns = ["name"] + PER + [c.replace("bp_", "y") for c in YCOLS] + ["unknown", "known", "total"]
    bands = a[a.band != "All"].pivot_table(index="ecode", columns="band", values="all_properties", aggfunc="sum").reindex(columns=BANDS).fillna(0)
    for b in BANDS:
        out["band_" + b] = bands[b].reindex(out.index).fillna(0)
    t = d3[(d3.geography == level) & (d3.band == "All")].set_index("ecode")
    out["bungalow"] = t["bungalow_total"]; out["flat"] = t["flat_mais_total"]; out["terraced"] = t["house_terraced_total"]
    out["semi"] = t["house_semi_total"]; out["detached"] = t["house_detached_total"]
    out["other_type"] = t["annexe"] + t["caravan_houseboat_mobilehome"] + t["unknown"]
    out["total_type"] = t["all_properties"]
    out.index.name = "code"
    return out


L = build("LSOA"); M = build("MSOA"); A = build("LAUA")
assert len(L) == 35672 and L.index.is_unique, len(L)
g = gpd.read_file(LSOA_GPKG).set_index("LSOA21CD")
assert set(g.index) == set(L.index)
g = g.to_crs(27700)
rp = g.geometry.representative_point()
# 2024 recodes of Barnsley and Sheffield (minor boundary change): VOA still uses the earlier codes
RECODE = {"E08000038": "E08000016", "E08000039": "E08000019"}
P = pd.DataFrame({"x": rp.x, "y": rp.y, "lad": g.LADCD_ACTIVE.replace(RECODE), "rgn": g.RGNCD.fillna("W92000004"),
                  "area_km2": g.geometry.area / 1e6}, index=g.index)
L = L.join(P[["lad", "rgn"]])
lanames = A["name"].to_dict()
L["lad_name"] = L.lad.map(lanames)
miss = L[L.lad_name.isna()].lad.unique()
assert len(miss) == 0, miss
if not SUF:
    P.to_parquet(os.path.join(SCR, "lsoa_points.parquet"))
L.to_csv(os.path.join(DATA if not SUF else SCR, f"lsoa_age{SUF}.csv"), float_format="%g")
M.to_csv(os.path.join(DATA if not SUF else SCR, f"msoa_age{SUF}.csv"), float_format="%g")
A.to_csv(os.path.join(DATA if not SUF else SCR, f"la_age{SUF}.csv"), float_format="%g")
# national and nation rows by band x period
rows = []
for code, nm in (("K04000001", "England and Wales"), ("E92000001", "England"), ("W92000004", "Wales")):
    a = d4[(d4.ecode == code)]
    a = a[a.geography.isin(["ENGWAL", "NATL"])]
    for r in a.itertuples():
        rows.append({"area": nm, "band": r.band, **{p: getattr(r, p.replace("2009on", "x")) if False else a.loc[r.Index, p] for p in PER},
                     **{c.replace("bp_", "y"): a.loc[r.Index, c] for c in YCOLS}, "unknown": r.unknown, "total": r.all_properties})
N = pd.DataFrame(rows)
N.to_csv(os.path.join(DATA if not SUF else SCR, f"nation_band_period{SUF}.csv"), index=False, float_format="%g")
print("LSOA", len(L), "MSOA", len(M), "LA", len(A), "homes", L.total.sum(), "national", N[(N.area == "England and Wales") & (N.band == "All")].total.iloc[0])

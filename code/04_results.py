"""Step 4: data/results.json, every number quoted anywhere (page, paper, blog, collage, post, README), from
SCR/analysis.json plus a few derived figures, with consistency checks."""
import numpy as np, pandas as pd
from common import *

A = jload(os.path.join(SCR, "analysis.json"))
L = pd.read_csv(os.path.join(DATA, "lsoa_age.csv"), index_col="code")
N = A["nat"]["England and Wales"]
R = dict(A)
R["meta"] = {"reference_date": "31 March 2025", "n_lsoa": int(len(L)), "n_lsoa_england": int((L.index.str[0] == "E").sum()),
             "n_lsoa_wales": int((L.index.str[0] == "W").sum()), "n_cities": A["main"]["n_city"], "catch_km": CATCH_KM,
             "homes_lsoa_sum": float(L.total.sum()), "homes_national": N["total"]}
yrs = N["years"]
R["newbuild"] = {"total_2009_2024": float(sum(v for k, v in yrs.items() if k != "2025")),
                 "peak_year": max((k for k in yrs if k != "2025"), key=lambda k: yrs[k]), "peak": float(max(v for k, v in yrs.items() if k != "2025")),
                 "low_year": min((k for k in yrs if k != "2025"), key=lambda k: yrs[k]), "low": float(min(v for k, v in yrs.items() if k != "2025"))}
# homes per year of each period (the periods have unequal lengths)
span = {"1900_1918": 19, "1919_1929": 11, "1930_1939": 10, "1945_1954": 10, "1955_1964": 10, "1965_1972": 8, "1973_1982": 10,
        "1983_1992": 10, "1993_1999": 7, "2000_2008": 9}
R["per_year"] = {p: N[p] / 100 * N["known"] / n for p, n in span.items()}
R["per_year"]["2009_2024"] = R["newbuild"]["total_2009_2024"] / 16
pb = A["pooled_bands"]
R["pooled_first"] = {"mean_year": pb[0]["mean_year"], "homes": pb[0]["homes"], **{g: pb[0][g] * 100 for g in GROUPS}}
R["pooled_second"] = {"mean_year": pb[1]["mean_year"], "homes": pb[1]["homes"], **{g: pb[1][g] * 100 for g in GROUPS}}
R["pooled_outer"] = {g: float(np.average([b[g] for b in pb[10:]], weights=[b["homes"] for b in pb[10:]]) * 100) for g in GROUPS}
R["profile"] = {PER[int(r["pidx"])]: r["mean"] for r in A["profile_mean_rel"]}
R["later_pct"] = {k: (np.exp(v) - 1) * 100 for k, v in A["later_vs_8392"].items()}
R["bins_pc"] = {"b1": A["m1_bins"][1]["b"], "b2": A["m1_bins"][2]["b"], "b19": A["m1_bins"][19]["b"]}
R["bin_oldest"] = int(np.argmin([b["mean_year"] for b in A["pooled_bands"]]))
# property types of the small areas within 1 km of a centre (not by period: the tables do not cross type with period)
X = pd.read_csv(os.path.join(DATA, "lsoa_measures.csv"), index_col="lsoa21cd")
inner = X.index[(X.km_to_centre < 1)]
R["inner_types"] = {t: float(L.loc[inner, t].sum() / L.loc[inner, "total_type"].sum() * 100) for t in ("flat", "terraced", "semi", "detached", "bungalow")}
R["inner_n_lsoa"] = int(len(inner))
CTc = pd.read_csv(os.path.join(DATA, "cities.csv"))
R["centres_offset_median"] = float(CTc.ne_offset_km[CTc.wikidata != "none"].median()); R["centres_offset_max"] = float(CTc.ne_offset_km.max())
R["pooled_bin3_interwar"] = pb[3]["interwar"] * 100
# per-city table (appendix)
PRc = pd.read_csv(os.path.join(DATA, "city_periods.csv"))
H4 = {r["city"]: r for r in A["h4"]["rows"]}
ct = []
for cty, t in PRc.groupby("city"):
    t = t.set_index("period")
    xs_ = X[X.city == cty]
    d_new = t.D.get("2009on"); d_old = (t.D["1983_1992"] * t.homes["1983_1992"] + t.D["1993_1999"] * t.homes["1993_1999"]) / (t.homes["1983_1992"] + t.homes["1993_1999"])
    from scipy.stats import spearmanr
    sub = t.loc[[p for p in PER[:7] if p in t.index]]
    ct.append({"city": cty, "n_lsoa": int(len(xs_)), "homes": float(xs_.known.sum()), "pre1919": float((xs_.pc_pre1919 * xs_.known).sum() / xs_.known.sum()),
               "new": float((xs_.pc_new * xs_.known).sum() / xs_.known.sum()), "rho": float(spearmanr(range(len(sub)), sub.D)[0]),
               "m3_pct": float((d_new / d_old - 1) * 100), "peak_pre1919": H4[cty]["peak_pre1919_km"], "peak_interwar": H4[cty]["peak_interwar_km"],
               "peak_5572": H4[cty]["peak_5572_km"], "order": H4[cty]["order"]})
R["city_table"] = sorted(ct, key=lambda r: -r["homes"])
# data checks: suppressed cells in the LSOA rows (all bands, period columns) and LSOA sums against local authority rows
import zipfile
z = zipfile.ZipFile(os.path.join(VOA, "CTSOP4.1.zip"))
d4 = pd.read_csv(z.open([n for n in z.namelist() if n.endswith(".csv")][0]), dtype=str, encoding="utf-8-sig")
v = d4[(d4.geography == "LSOA") & (d4.band == "All")][PCOLS + YCOLS + ["bp_unkw"]].to_numpy().ravel()
LAr = pd.read_csv(os.path.join(DATA, "la_age.csv"), index_col="code")
dd = (L.groupby("lad").total.sum() / LAr.total - 1).abs() * 100
lr = d4[(d4.geography == "LSOA") & (d4.band == "All")]
nd = {k: int((lr[c] == "-").to_numpy().sum()) for k, c in (("periods", PCOLS), ("years", YCOLS), ("unknown", ["bp_unkw"]))}
R["data_checks"] = {"dash_in_years_pc": nd["years"] / sum(nd.values()) * 100, "cells": int(len(v)), "dash_pc": float((v == "-").mean() * 100), "zero_pc": float((v == "0").mean() * 100),
                    "la_sum_diff_median_pc": float(dd.median()), "la_sum_diff_max_pc": float(dd.max())}
ctab = {r["city"]: r for r in R["city_table"]}
R["city_rho_neg"] = [r["city"] for r in R["city_table"] if r["rho"] <= 0]
R["city_m3_pos"] = sorted([r["city"] for r in R["city_table"] if r["m3_pct"] > 0])
R["city_m3_min"] = min(R["city_table"], key=lambda r: r["m3_pct"])
R["london"] = ctab["London"]
# checks
assert abs(R["meta"]["homes_lsoa_sum"] / N["total"] - 1) < 0.001
assert R["meta"]["n_lsoa"] == 35672 and A["n_lsoa_known"] == 35672
assert sum(A["lsoa_median_counts"].values()) == 35672
assert abs(sum(N[p] for p in PER) - 100) < 1e-6
assert A["main"]["n_city"] == 34
jsave(R, os.path.join(DATA, "results.json"), indent=1)
print("results.json", len(json.dumps(R)) // 1024, "KB; new-build peak", R["newbuild"], "oldest band", R["bin_oldest"])

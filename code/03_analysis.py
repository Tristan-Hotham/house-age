"""Step 3: every estimand and model of the plan in NOTES.md. Writes SCR/analysis.json (read by 04_results.py),
data/lsoa_measures.csv (shares, median period, mean year, city and distance per LSOA), data/city_periods.csv (mean
distance from the centre of each period's homes, by city), data/city_bands.csv (shares by 1 km band, by city),
data/la_rank.csv, data/models.csv."""
import numpy as np, pandas as pd, geopandas as gpd
import statsmodels.formula.api as smf
from scipy import stats
from common import *

rng = np.random.default_rng(1)
clean = lambda s_: re.sub(r" UA$", "", str(s_).split(" / ")[0])
P = pd.read_parquet(os.path.join(SCR, "lsoa_points.parquet"))
CT = pd.read_csv(os.path.join(DATA, "cities.csv"))
NC = len(CT)
OUT = {}


def measures(L, pre1900=1875.0):
    """Shares of known homes by period, median period index, mean build year, unknown share."""
    M = pd.DataFrame(index=L.index)
    K = L["known"].to_numpy(float)
    cnt = L[PER].to_numpy(float)
    with np.errstate(invalid="ignore", divide="ignore"):
        sh = cnt / K[:, None]
    for j, p in enumerate(PER):
        M["s_" + p] = sh[:, j]
    for g, ps in GROUPS.items():
        M["g_" + g] = L[ps].sum(axis=1) / K
    cum = np.cumsum(cnt, axis=1)
    M["median_idx"] = np.where(K > 0, (cum >= K[:, None] / 2).argmax(axis=1), -1)
    yrs = np.array([pre1900] + [MID[p] for p in PER[1:11]] + list(range(2009, 2026)), float)
    cnty = np.column_stack([cnt[:, :11], L[[c.replace("bp_", "y") for c in YCOLS]].to_numpy(float)])
    M["mean_year"] = (cnty * yrs).sum(axis=1) / K
    M["unknown_share"] = L["unknown"] / (L["unknown"] + K)
    M["known"] = K
    return M


def assign(xy_c, x, y):
    d = np.hypot(x[:, None] - xy_c[None, :, 0], y[:, None] - xy_c[None, :, 1]) / 1000
    j = d.argmin(axis=1)
    return j, d[np.arange(len(x)), j]


def demean(v, g, w):
    """Weighted within-group demeaning."""
    s = pd.DataFrame({"v": v * w, "w": w, "g": g}).groupby("g").sum()
    m = (s.v / s.w).reindex(g).to_numpy()
    return v - m


def m1_fast(y, d, g, w):
    """Weighted slope of y on d with group fixed effects (point estimate only)."""
    yd, dd = demean(y, g, w), demean(d, g, w)
    return float((w * yd * dd).sum() / (w * dd * dd).sum())


def m2_frame(L, j, d, catch, periods=PER[:7]):
    rows = []
    inc = d <= catch
    for c in range(NC):
        s = inc & (j == c)
        for k, p in enumerate(periods):
            n = L[p].to_numpy(float)[s]
            if n.sum() > 0:
                rows.append({"city": CT.city[c], "pidx": k, "period": p, "D": float((n * d[s]).sum() / n.sum()), "n": float(n.sum())})
    return pd.DataFrame(rows)


def m2_fast(F):
    F = F[F.D > 0]
    return m1_fast(np.log(F.D.to_numpy()), F.pidx.to_numpy(float), F.city.to_numpy(), np.ones(len(F)))


def cohort_D(L, j, d, catch, cols):
    """Mean distance of homes in `cols` (list of period columns) for each city."""
    inc = d <= catch
    n = L[cols].sum(axis=1).to_numpy(float)
    out = np.full(NC, np.nan)
    for c in range(NC):
        s = inc & (j == c)
        if n[s].sum() > 0:
            out[c] = (n[s] * d[s]).sum() / n[s].sum()
    return out


def m3(L, j, d, catch):
    a = cohort_D(L, j, d, catch, ["2009on"]); b = cohort_D(L, j, d, catch, ["1983_1992", "1993_1999"])
    diff = np.log(a) - np.log(b)
    diff = diff[np.isfinite(diff)]
    m, se = diff.mean(), diff.std(ddof=1) / np.sqrt(len(diff))
    t = stats.t.ppf(0.975, len(diff) - 1)
    return {"mean": float(m), "lo": float(m - t * se), "hi": float(m + t * se), "n": int(len(diff)),
            "neg": int((diff < 0).sum()), "pct_change": float((np.exp(m) - 1) * 100),
            "pct_lo": float((np.exp(m - t * se) - 1) * 100), "pct_hi": float((np.exp(m + t * se) - 1) * 100)}


def run_models(L, M, xy, catch=CATCH_KM, cluster="lad", keep=None, full=True):
    x, y = P.x.reindex(L.index).to_numpy(), P.y.reindex(L.index).to_numpy()
    j, d = assign(xy, x, y)
    sel = (d <= catch) & (M.known.to_numpy() > 0)
    if keep is not None:
        sel &= keep
    D = pd.DataFrame({"y": M.mean_year.to_numpy()[sel], "d": d[sel], "city": CT.city.to_numpy()[j[sel]],
                      "lad": L.lad.to_numpy()[sel], "w": M.known.to_numpy()[sel]})
    res = {"n_lsoa": int(sel.sum()), "n_homes": float(D.w.sum()), "n_lad": int(D.lad.nunique()), "n_city": int(D.city.nunique())}
    if full:
        f = smf.wls("y ~ C(city) + d", data=D, weights=D.w).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(D[cluster])[0]})
        ci = f.conf_int().loc["d"]
        res.update({"m1_b": float(f.params["d"]), "m1_lo": float(ci[0]), "m1_hi": float(ci[1]), "m1_p": float(f.pvalues["d"])})
    else:
        res["m1_b"] = m1_fast(D.y.to_numpy(), D.d.to_numpy(), D.city.to_numpy(), D.w.to_numpy())
    Lk = L if keep is None else L[keep]
    jk, dk = (j, d) if keep is None else (j[keep], d[keep])
    F = m2_frame(Lk, jk, dk, catch)
    if full:
        F2 = F[F.D > 0].copy(); F2["lD"] = np.log(F2.D)
        g = smf.ols("lD ~ C(city) + pidx", data=F2).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(F2.city)[0]})
        ci = g.conf_int().loc["pidx"]
        res.update({"m2_b": float(g.params["pidx"]), "m2_lo": float(ci[0]), "m2_hi": float(ci[1]), "m2_p": float(g.pvalues["pidx"]),
                    "m2_n": int(len(F2)), "m2_pct": float((np.exp(g.params["pidx"]) - 1) * 100),
                    "m2_pct_lo": float((np.exp(ci[0]) - 1) * 100), "m2_pct_hi": float((np.exp(ci[1]) - 1) * 100)})
        rho = F2.groupby("city").apply(lambda t: stats.spearmanr(t.pidx, t.D)[0] if len(t) > 2 else np.nan, include_groups=False)
        res["m2_rho_pos"] = int((rho > 0).sum()); res["m2_rho_n"] = int(rho.notna().sum()); res["m2_rho_median"] = float(rho.median())
        res["m3"] = m3(Lk, jk, dk, catch)
    else:
        res["m2_b"] = m2_fast(F)
    return res, j, d, F


L = pd.read_csv(os.path.join(DATA, "lsoa_age.csv"), index_col="code")
M = measures(L)
XY = CT[["x", "y"]].to_numpy(float)
XY_NE = CT[["ne_x", "ne_y"]].to_numpy(float)
main, J, Dk, F = run_models(L, M, XY)
OUT["main"] = main
print("main", {k: v for k, v in main.items() if k != "m3"}, main["m3"])

# ---------- bins, quadratic (R9), cluster by city (R8)
x, y = P.x.reindex(L.index).to_numpy(), P.y.reindex(L.index).to_numpy()
sel = (Dk <= CATCH_KM) & (M.known.to_numpy() > 0)
B = pd.DataFrame({"y": M.mean_year[sel].to_numpy(), "d": Dk[sel], "city": CT.city.to_numpy()[J[sel]], "lad": L.lad[sel].to_numpy(),
                  "w": M.known[sel].to_numpy()})
B["bin"] = np.minimum(B.d.astype(int), 19)
fb = smf.wls("y ~ C(city) + C(bin)", data=B, weights=B.w).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(B.lad)[0]})
bins = [{"bin": 0, "b": 0.0, "lo": 0.0, "hi": 0.0}]
for k in range(1, 20):
    nm = f"C(bin)[T.{k}]"; ci = fb.conf_int().loc[nm]
    bins.append({"bin": k, "b": float(fb.params[nm]), "lo": float(ci[0]), "hi": float(ci[1])})
OUT["m1_bins"] = bins
B["d2"] = B.d ** 2
fq = smf.wls("y ~ C(city) + d + d2", data=B, weights=B.w).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(B.lad)[0]})
OUT["m1_quad"] = {"b1": float(fq.params["d"]), "b2": float(fq.params["d2"]), "p2": float(fq.pvalues["d2"]),
                  "turn_km": float(-fq.params["d"] / (2 * fq.params["d2"])) if fq.params["d2"] < 0 else None}
fc = smf.wls("y ~ C(city) + d", data=B, weights=B.w).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(B.city)[0]})
ci = fc.conf_int().loc["d"]
OUT["m1_cluster_city"] = {"b": float(fc.params["d"]), "lo": float(ci[0]), "hi": float(ci[1])}
# raw (unweighted-by-city) mean year by 1 km band, and group shares by band, all cities pooled and per city
B["k"] = M.known[sel].to_numpy()
for gname in GROUPS:
    B["n_" + gname] = (M["g_" + gname][sel] * M.known[sel]).to_numpy()
B["n_yr"] = B.y * B.k
band_rows = []
for (cty, b), t in B.groupby(["city", "bin"]):
    band_rows.append({"city": cty, "bin": int(b), "homes": float(t.k.sum()), "mean_year": float(t.n_yr.sum() / t.k.sum()),
                      **{g: float(t["n_" + g].sum() / t.k.sum()) for g in GROUPS}})
CB = pd.DataFrame(band_rows)
CB.to_csv(os.path.join(DATA, "city_bands.csv"), index=False, float_format="%.4f")
pool = B.groupby("bin").apply(lambda t: pd.Series({"homes": t.k.sum(), "mean_year": t.n_yr.sum() / t.k.sum(),
                                                    **{g: t["n_" + g].sum() / t.k.sum() for g in GROUPS}}), include_groups=False)
OUT["pooled_bands"] = pool.reset_index().to_dict("records")

# ---------- H4 interwar belt: argmax band (bands with at least 1,000 known homes)
h4 = []
for cty, t in CB[CB.homes >= 1000].groupby("city"):
    t = t.set_index("bin")
    a = int(t.pre1919.idxmax()); b = int(t.interwar.idxmax())
    # 1955 to 1972 share by band
    s = sel & (CT.city.to_numpy()[J] == cty)
    n5572 = (L[["1955_1964", "1965_1972"]].sum(axis=1)).to_numpy()[s]
    bb = np.minimum(Dk[s].astype(int), 19)
    kk = M.known.to_numpy()[s]
    sh = pd.Series(n5572).groupby(bb).sum() / pd.Series(kk).groupby(bb).sum()
    sh = sh[pd.Series(kk).groupby(bb).sum() >= 1000]
    c_ = int(sh.idxmax())
    h4.append({"city": cty, "peak_pre1919_km": a, "peak_interwar_km": b, "peak_5572_km": c_, "order": bool(a < b < c_),
               "order_weak": bool(a <= b <= c_), "max_interwar": float(t.interwar.max())})
H4 = pd.DataFrame(h4)
OUT["h4"] = {"n": len(H4), "order": int(H4.order.sum()), "order_weak": int(H4.order_weak.sum()),
             "median_pre1919": float(H4.peak_pre1919_km.median()), "median_interwar": float(H4.peak_interwar_km.median()),
             "median_5572": float(H4.peak_5572_km.median()), "rows": H4.to_dict("records")}

# ---------- cohort distance profile: all 12 periods, by city, relative to the city's all-homes mean distance
prof = []
for c in range(NC):
    s = sel & (J == c)
    allD = (M.known.to_numpy()[s] * Dk[s]).sum() / M.known.to_numpy()[s].sum()
    for k, p in enumerate(PER):
        n = L[p].to_numpy(float)[s]
        if n.sum() > 0:
            prof.append({"city": CT.city[c], "pidx": k, "period": p, "D": (n * Dk[s]).sum() / n.sum(), "rel": (n * Dk[s]).sum() / n.sum() / allD, "homes": n.sum()})
PR = pd.DataFrame(prof)
PR.to_csv(os.path.join(DATA, "city_periods.csv"), index=False, float_format="%.4f")
OUT["profile_mean_rel"] = PR.groupby("pidx").rel.agg(["mean", "median"]).reset_index().to_dict("records")
OUT["profile_peak_pidx_median"] = float(PR.loc[PR.groupby("city").D.idxmax()].pidx.median())
OUT["profile_peak_by_city"] = PR.loc[PR.groupby("city").D.idxmax()][["city", "period"]].to_dict("records")
# every later period against 1983-1992 (descriptive profile for H3)
pr = PR.pivot(index="city", columns="period", values="D")
OUT["later_vs_8392"] = {p: float((np.log(pr[p]) - np.log(pr["1983_1992"])).mean()) for p in ["1993_1999", "2000_2008", "2009on"]}

# ---------- robustness
R = {}
Ld = pd.read_csv(os.path.join(SCR, "lsoa_age_dash2.5.csv"), index_col="code")
R["dash"] = run_models(Ld, measures(Ld), XY)[0]
for v in (1850.0, 1890.0):
    R[f"pre{int(v)}"] = run_models(L, measures(L, v), XY)[0]
for ck in (10.0, 30.0):
    R[f"catch{int(ck)}"] = run_models(L, M, XY, catch=ck)[0]
R["ne_centres"] = run_models(L, M, XY_NE)[0]
R["unknown2"] = run_models(L, M, XY, keep=(M.unknown_share.fillna(1).to_numpy() < 0.02))[0]
R["no_london"] = run_models(L, M, XY, keep=(L.rgn.to_numpy() != "E12000007"))[0]
loro = {}
for rg, nm in REGIONS.items():
    loro[nm] = run_models(L, M, XY, keep=(L.rgn.to_numpy() != rg))[0]
R["loro"] = {k: {"m1_b": v["m1_b"], "m1_lo": v["m1_lo"], "m1_hi": v["m1_hi"], "m2_b": v["m2_b"], "m2_lo": v["m2_lo"], "m2_hi": v["m2_hi"],
                 "m3": v["m3"]["mean"], "m3_lo": v["m3"]["lo"], "m3_hi": v["m3"]["hi"], "n_lsoa": v["n_lsoa"], "n_city": v["n_city"]} for k, v in loro.items()}
OUT["robust"] = R
# placebo: centres moved 10 km in a random direction (200 draws)
pl = []
for it in range(200):
    th = rng.uniform(0, 2 * np.pi, NC)
    xy = XY + 10000 * np.column_stack([np.cos(th), np.sin(th)])
    r = run_models(L, M, xy, full=False)[0]
    pl.append((r["m1_b"], r["m2_b"]))
pl = np.array(pl)
OUT["placebo"] = {"draws": 200, "m1_p95": float(np.percentile(pl[:, 0], 95)), "m1_mean": float(pl[:, 0].mean()), "m1_max": float(pl[:, 0].max()),
                  "m1_share_ge_real": float((pl[:, 0] >= main["m1_b"]).mean()), "m2_p95": float(np.percentile(pl[:, 1], 95)),
                  "m2_mean": float(pl[:, 1].mean()), "m2_max": float(pl[:, 1].max()), "m2_share_ge_real": float((pl[:, 1] >= main["m2_b"]).mean())}
print("placebo", OUT["placebo"])

# MSOA replication (R8)
Mm = pd.read_csv(os.path.join(DATA, "msoa_age.csv"), index_col="code")
gm = gpd.read_file(os.path.join(GEO, "msoa21_bsc.geojson"))
mc = [c for c in gm.columns if c.upper().startswith("MSOA21CD")][0]
gm = gm.set_index(mc).to_crs(27700)
rpm = gm.geometry.representative_point()
Pm = pd.DataFrame({"x": rpm.x, "y": rpm.y})
MM = measures(Mm)
xm, ym = Pm.x.reindex(Mm.index).to_numpy(), Pm.y.reindex(Mm.index).to_numpy()
jm, dm = assign(XY, xm, ym)
ok = (dm <= CATCH_KM) & (MM.known.to_numpy() > 0) & np.isfinite(xm)
Dm = pd.DataFrame({"y": MM.mean_year.to_numpy()[ok], "d": dm[ok], "city": CT.city.to_numpy()[jm[ok]], "w": MM.known.to_numpy()[ok]})
fm = smf.wls("y ~ C(city) + d", data=Dm, weights=Dm.w).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(Dm.city)[0]})
ci = fm.conf_int().loc["d"]
Fm = m2_frame(Mm, jm, np.where(np.isfinite(dm), dm, 1e9), CATCH_KM)
OUT["msoa"] = {"n": int(ok.sum()), "m1_b": float(fm.params["d"]), "m1_lo": float(ci[0]), "m1_hi": float(ci[1]), "m2_b": m2_fast(Fm)}

# ---------- descriptives D1 to D5
Nb = pd.read_csv(os.path.join(DATA, "nation_band_period.csv"))
nat = {}
for area in ("England and Wales", "England", "Wales"):
    a = Nb[(Nb.area == area) & (Nb.band == "All")].iloc[0]
    kn = sum(a[p] for p in PER)
    nat[area] = {"total": float(a.total), "known": float(kn), "unknown": float(a.unknown), "unknown_share": float(a.unknown / (a.unknown + kn) * 100),
                 **{p: float(a[p] / kn * 100) for p in PER}, **{g: float(sum(a[p] for p in ps) / kn * 100) for g, ps in GROUPS.items()},
                 "years": {str(yy): float(a[f"y{yy}"]) for yy in range(2009, 2026)}}
    cum = np.cumsum([a[p] for p in PER]) / kn
    nat[area]["median_idx"] = int((cum >= 0.5).argmax())
OUT["nat"] = nat
# D2 LSOA median period distribution
mi = M.median_idx[M.known > 0]
OUT["lsoa_median_counts"] = {PER[k]: int((mi == k).sum()) for k in range(12)}
OUT["n_lsoa"] = int(len(M)); OUT["n_lsoa_known"] = int((M.known > 0).sum())
grp_of = {p: g for g, ps in GROUPS.items() for p in ps}
gm_ = mi.map(lambda k: grp_of[PER[k]])
OUT["lsoa_median_groups"] = {g: int((gm_ == g).sum()) for g in GROUPS}
OUT["lsoa_median_groups_pc"] = {g: float((gm_ == g).mean() * 100) for g in GROUPS}
OUT["lsoa_majority"] = {g: int((M["g_" + g] >= 0.5).sum()) for g in GROUPS}
OUT["lsoa_unknown_gt10"] = int((M.unknown_share > 0.10).sum())
OUT["lsoa_unknown_gt50"] = int((M.unknown_share > 0.50).sum())
# oldest and newest LSOAs by mean year (at least 300 known homes)
big = M[M.known >= 300]
for lab, idx in (("oldest", big.mean_year.nsmallest(5).index), ("newest", big.mean_year.nlargest(5).index)):
    OUT[lab + "_lsoa"] = [{"code": c, "name": L.name[c], "lad": clean(L.lad_name[c]), "mean_year": float(M.mean_year[c]), "known": float(M.known[c]),
                           "pre1919": float(M.g_pre1919[c] * 100), "new": float(M.g_new[c] * 100)} for c in idx]
OUT["lsoa_all_pre1919_n"] = int((M.g_pre1919 >= 0.9).sum())
OUT["lsoa_all_new_n"] = int((M.g_new >= 0.9).sum())
# D3 local authorities
A = pd.read_csv(os.path.join(DATA, "la_age.csv"), index_col="code")
MA = measures(A)
A2 = pd.DataFrame({"name": A.name.map(clean), "homes": A.total, "known": MA.known,
                   "pre1919": MA.g_pre1919 * 100, "interwar": MA.g_interwar * 100, "postwar": MA.g_postwar * 100,
                   "new": MA.g_new * 100, "mean_year": MA.mean_year, "median_idx": MA.median_idx, "unknown_share": MA.unknown_share * 100})
A2["median_period"] = A2.median_idx.map(lambda k: PER_LABEL[k])
A2.to_csv(os.path.join(DATA, "la_rank.csv"), float_format="%.3f")
rec = lambda t: [{"code": c, "name": r["name"], "pre1919": float(r.pre1919), "new": float(r.new), "mean_year": float(r.mean_year),
                  "interwar": float(r.interwar), "postwar": float(r.postwar), "median": r.median_period, "homes": float(r.homes)} for c, r in t.iterrows()]
OUT["la_oldest_pre1919"] = rec(A2.nlargest(10, "pre1919")); OUT["la_youngest_pre1919"] = rec(A2.nsmallest(10, "pre1919"))
OUT["la_newest"] = rec(A2.nlargest(10, "new")); OUT["la_interwar"] = rec(A2.nlargest(10, "interwar")); OUT["la_postwar"] = rec(A2.nlargest(10, "postwar"))
OUT["la_oldest_mean"] = rec(A2.nsmallest(10, "mean_year")); OUT["la_newest_mean"] = rec(A2.nlargest(10, "mean_year"))
OUT["la_unknown_top"] = [{"name": r["name"], "unknown_share": float(r.unknown_share)} for _, r in A2.nlargest(5, "unknown_share").iterrows()]
OUT["n_la"] = int(len(A2))
OUT["la_median_counts"] = {PER[k]: int((A2.median_idx == k).sum()) for k in range(12)}
# D4 new-build frontier
fr = M[(M.g_new >= 0.5) & (M.known > 0)]
OUT["frontier_n"] = int(len(fr)); OUT["frontier_homes_new"] = float((fr.g_new * fr.known).sum())
OUT["frontier_by_la"] = [{"name": n, "n": int(k)} for n, k in L.loc[fr.index].lad_name.map(clean).value_counts().head(10).items()]
OUT["frontier_by_region"] = {REGIONS[k]: int(v) for k, v in L.loc[fr.index].rgn.value_counts().items()}
newh = (M.g_new * M.known)
OUT["new_share_in_top10pc_lsoa"] = float(newh.sort_values(ascending=False).head(len(M) // 10).sum() / newh.sum() * 100)
# D5 bands by period (England, Wales) and types
bands = {}
for area, bl in (("England", list("ABCDEFGH")), ("Wales", list("ABCDEFGHI"))):
    t = Nb[(Nb.area == area) & (Nb.band.isin(bl))].set_index("band")
    tab = {}
    for p in PER:
        col = t[p]; tot = col.sum()
        tab[p] = {"AB": float(col[["A", "B"]].sum() / tot * 100), "FGH": float(col[[b for b in bl if b >= "F"]].sum() / tot * 100),
                  "mean_band": float(sum((i + 1) * col[b] for i, b in enumerate(bl)) / tot), "A": float(col["A"] / tot * 100)}
    bands[area] = tab
OUT["bands"] = bands
T = L[["bungalow", "flat", "terraced", "semi", "detached"]].div(L.total_type, axis=0)
ok = (M.known > 0) & (L.total_type > 0)
wcorr = lambda a, b, w: float(np.cov(a, b, aweights=w)[0, 1] / np.sqrt(np.cov(a, a, aweights=w)[0, 0] * np.cov(b, b, aweights=w)[0, 0]))
OUT["type_corr"] = {f"{g}_{t}": wcorr(M["g_" + g][ok], T[t][ok], M.known[ok]) for g in ("pre1919", "interwar", "postwar", "new") for t in T.columns}
# type mix by LSOA median group (homes-weighted)
tm = {}
for g in GROUPS:
    s = ok & (gm_.reindex(M.index) == g)
    tm[g] = {t: float(L.loc[s, t].sum() / L.loc[s, "total_type"].sum() * 100) for t in T.columns}
OUT["type_by_median_group"] = tm
# regions
reg = {}
for rg, nm in REGIONS.items():
    s = (L.rgn == rg)
    kn = L.loc[s, "known"].sum()
    reg[nm] = {g: float(L.loc[s, ps].sum().sum() / kn * 100) for g, ps in GROUPS.items()}
    reg[nm]["mean_year"] = float((M.mean_year[s] * M.known[s]).sum() / M.known[s].sum())
OUT["regions"] = reg
# exploratory (added after the plan): within-LA association between mean build year and the Council Tax band index (England)
E = L[(L.rgn != "W92000004") & (M.known > 0)].copy()
E["band_idx"] = sum((i + 1) * E["band_" + b] for i, b in enumerate("ABCDEFGH")) / E[["band_" + b for b in "ABCDEFGH"]].sum(axis=1)
E["my"] = M.mean_year[E.index]; E["w"] = M.known[E.index]
for t in ("flat", "terraced", "semi", "detached", "bungalow"):
    E["t_" + t] = L.loc[E.index, t] / L.loc[E.index, "total_type"]
fx = smf.wls("band_idx ~ C(lad) + I(my/10) + t_flat + t_terraced + t_semi + t_bungalow", data=E, weights=E.w).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(E.lad)[0]})
ci = fx.conf_int().loc["I(my / 10)"]
OUT["explor_band"] = {"b_decade": float(fx.params["I(my / 10)"]), "lo": float(ci[0]), "hi": float(ci[1]), "n": int(len(E)), "n_lad": int(E.lad.nunique())}
# save the LSOA measures
X = pd.DataFrame({"name": L.name, "lad": L.lad, "lad_name": L.lad_name.map(clean), "region": L.rgn.map(REGIONS),
                  "homes": L.total, "known": M.known, "unknown_share": (M.unknown_share * 100).round(2)})
for p in PER:
    X["pc_" + p] = (M["s_" + p] * 100).round(2)
for g in GROUPS:
    X["pc_" + g] = (M["g_" + g] * 100).round(2)
X["median_period"] = M.median_idx.map(lambda k: PER_LABEL[k] if k >= 0 else "")
X["mean_year"] = M.mean_year.round(1)
X["city"] = np.where(Dk <= CATCH_KM, CT.city.to_numpy()[J], "")
X["km_to_centre"] = np.where(Dk <= CATCH_KM, np.round(Dk, 2), np.nan)
X.index.name = "lsoa21cd"
X.to_csv(os.path.join(DATA, "lsoa_measures.csv"))
# models table
rowsm = [{"model": "M1 mean build year on distance (years per km), city FE, LAD clusters", **{k: main[k] for k in ("m1_b", "m1_lo", "m1_hi", "m1_p", "n_lsoa", "n_lad", "n_city")}},
         {"model": "M2 log mean distance on period order (pre-1900 to 1965-72), city FE, city clusters", "m1_b": main["m2_b"], "m1_lo": main["m2_lo"], "m1_hi": main["m2_hi"], "m1_p": main["m2_p"], "n_lsoa": main["m2_n"]},
         {"model": "M3 log mean distance, 2009 onwards minus 1983-1999 (mean over cities)", "m1_b": main["m3"]["mean"], "m1_lo": main["m3"]["lo"], "m1_hi": main["m3"]["hi"], "n_lsoa": main["m3"]["n"]}]
pd.DataFrame(rowsm).rename(columns={"m1_b": "estimate", "m1_lo": "ci_lo", "m1_hi": "ci_hi", "m1_p": "p", "n_lsoa": "n"}).to_csv(os.path.join(DATA, "models.csv"), index=False, float_format="%.5g")
OUT["bin_fit_n"] = int(fb.nobs)
jsave(OUT, os.path.join(SCR, "analysis.json"), indent=1)
print("H4", OUT["h4"]["order"], "/", OUT["h4"]["n"], "m1 quad", OUT["m1_quad"], "msoa", OUT["msoa"])

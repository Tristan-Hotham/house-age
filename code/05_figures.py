"""Step 5: figures for the paper (release/paper/f_*.pdf), the blog (release/blog/b_*.png, 1800 px) and the page (img/*.jpg)."""
import numpy as np, pandas as pd
from matplotlib.patches import Patch, Rectangle
from matplotlib.lines import Line2D
from figstyle import *

R = jload(f"{DATA}/results.json")
X = pd.read_csv(f"{DATA}/lsoa_measures.csv", index_col="lsoa21cd")
CT = pd.read_csv(f"{DATA}/cities.csv")
CB = pd.read_csv(f"{DATA}/city_bands.csv")
PR = pd.read_csv(f"{DATA}/city_periods.csv")
LA = pd.read_csv(f"{DATA}/la_rank.csv", index_col="code")
G = lsoa_shapes()
G = G.join(X[["median_period", "mean_year", "pc_pre1919", "pc_new", "pc_interwar"]])
G["mi"] = G.median_period.map({l: k for k, l in enumerate(PER_LABEL)})
cmap, norm = period_cmap()
col_of = lambda k: PCOL[int(k)] if k == k and k >= 0 else NODATA
G["col"] = G.mi.map(col_of)
EXT = (130000, 660000, 5000, 660000)


def period_legend(ax, loc="upper left", fs=9.5, title="Median build period of homes", anchor=None, ncol=1):
    h = [Patch(facecolor=c, label=l) for c, l in zip(PCOL, PER_LABEL)]
    lg = ax.legend(handles=h, loc=loc, fontsize=fs, title=title, title_fontsize=fs + 1, frameon=True, ncol=ncol,
                   bbox_to_anchor=anchor, borderpad=0.6, handlelength=1.4)
    lg.get_frame().set_facecolor(PAPER); lg.get_frame().set_edgecolor(RULE)
    return lg


def city_box(ax, city, half=14000):
    c = CT[CT.city == city].iloc[0]
    return (c.x - half, c.x + half, c.y - half, c.y + half)


def inset(fig, rect, city, half=14000, title=None):
    a = fig.add_axes(rect)
    e = city_box(None, city, half)
    context_land(a, e)
    s = G.cx[e[0] - 2000:e[1] + 2000, e[2] - 2000:e[3] + 2000]
    draw_polys(a, s.geometry, s.col, zorder=2)
    c = CT[CT.city == city].iloc[0]
    a.plot([c.x], [c.y], marker="+", ms=11, mew=2, color=FG, zorder=5)
    a.set_title(title or city, loc="left", fontproperties=DISPB, fontsize=12, color=FG, pad=3)
    for s_ in a.spines.values():
        s_.set_visible(True); s_.set_color(RULE)
    return a


# ---------------------------------------------------------------- 1. the national map with city insets
fig = plt.figure(figsize=(12, 9.0), facecolor=PAPER)
ax = fig.add_axes([0.0, 0.0, 0.58, 1.0])
context_land(ax, EXT)
draw_polys(ax, G.geometry, G.col)
period_legend(ax, loc="upper left", anchor=(0.005, 0.995), ncol=2, fs=8.5, title="Median home built")
ax.text(0.13, 0.015, "Valuation Office Agency, Council Tax stock of properties 2025; ONS LSOA 2021 boundaries", transform=ax.transAxes, fontsize=8, color=MUT)
for k, (city, title) in enumerate([("London", "London"), ("Manchester", "Manchester"), ("Birmingham", "Birmingham"),
                                   ("Leeds", "Leeds and Bradford"), ("Bristol", "Bristol"), ("Newcastle upon Tyne", "Newcastle and Gateshead")]):
    r, c = divmod(k, 2)
    inset(fig, [0.595 + c * 0.205, 0.655 - r * 0.31, 0.195, 0.262], city, half=16000 if city == "London" else 11000, title=title)
fig.text(0.595, 0.985, "Each small area (LSOA) coloured by the build period of its median home. + marks the city centre.",
         fontsize=9, color=MUT, va="top", wrap=True)
savefig(fig, "map", blog="map", img="map")

# ---------------------------------------------------------------- 2. the national stock by period, and per year
N = R["nat"]["England and Wales"]
fig, axs = plt.subplots(1, 2, figsize=(12, 4.6), facecolor=PAPER, gridspec_kw={"width_ratios": [1.15, 1]})
a = axs[0]
vals = [N[p] for p in PER]
a.bar(range(12), vals, color=PCOL, edgecolor="white", lw=0.6)
for i, v in enumerate(vals):
    a.text(i, v + 0.3, f"{v:.0f}%", ha="center", fontsize=9, color=FG)
a.set_xticks(range(12)); a.set_xticklabels(PER_SHORT, rotation=45, ha="right", fontsize=9)
a.set_ylabel("Share of homes of known age (%)"); style_axes(a)
a.set_title("Homes standing in 2025 by build period", loc="left", fontproperties=DISPB, fontsize=13, color=FG)
a = axs[1]
yrs = [str(y) for y in range(2009, 2025)]
a.bar(range(len(yrs)), [N["years"][y] / 1000 for y in yrs], color=PCOL[-1], edgecolor="white", lw=0.5)
py = R["per_year"]
seg = [("1900_1918", 1900, 1918), ("1919_1929", 1919, 1929), ("1930_1939", 1930, 1939), ("1945_1954", 1945, 1954), ("1955_1964", 1955, 1964),
       ("1965_1972", 1965, 1972), ("1973_1982", 1973, 1982), ("1983_1992", 1983, 1992), ("1993_1999", 1993, 1999), ("2000_2008", 2000, 2008)]
a2 = a.inset_axes([0.0, 0.0, 1, 1]); a2.remove()
a.set_xticks(range(0, len(yrs), 3)); a.set_xticklabels(yrs[::3], fontsize=9)
a.set_ylabel("Homes still standing, thousands")
a.set_title("Built 2009 to 2024, year by year", loc="left", fontproperties=DISPB, fontsize=13, color=FG)
style_axes(a)
fig.tight_layout()
savefig(fig, "national", blog="national", img="national")

# ---------------------------------------------------------------- 2b. homes per year of each period (paper)
fig, a = plt.subplots(figsize=(10, 3.8), facecolor=PAPER)
for p, y0, y1 in seg:
    a.add_patch(Rectangle((y0, 0), y1 - y0 + 1, py[p] / 1000, facecolor=PCOL[PER.index(p)], edgecolor="white", lw=0.6))
for y in yrs:
    a.add_patch(Rectangle((int(y), 0), 1, N["years"][y] / 1000, facecolor=PCOL[-1], edgecolor="white", lw=0.4))
a.set_xlim(1898, 2026); a.set_ylim(0, max(max(py.values()), max(N["years"].values())) / 1000 * 1.12)
a.axvspan(1939.5, 1945, color="#EDEBE5", zorder=0); a.text(1942.2, 5, "no age code\n1940 to 1944", ha="center", fontsize=8, color=MUT, rotation=90, va="bottom")
a.set_ylabel("Surviving homes per year\nof the period, thousands"); style_axes(a)
a.set_title("Homes standing in 2025, per year of their build period (before 1900 not shown)", loc="left", fontproperties=DISPB, fontsize=12.5, color=FG)
fig.tight_layout()
savefig(fig, "peryear")

# ---------------------------------------------------------------- 3. rings: pooled shares by distance band
PB = pd.DataFrame(R["pooled_bands"])
order = ["pre1919", "interwar", "postwar", "late20", "early21", "new"]
fig, a = plt.subplots(figsize=(11, 5.2), facecolor=PAPER)
xs = np.r_[PB.bin.to_numpy(), 20]
base = np.zeros(len(PB) + 1)
for g in order:
    v = np.r_[PB[g].to_numpy(), PB[g].to_numpy()[-1]] * 100
    a.fill_between(xs, base, base + v, color=GCOL[g], step="post", lw=0, label=GROUP_LABEL[g])
    base += v
a.set_xlim(0, 20); a.set_ylim(0, 100)
a.set_xlabel("Distance from the city centre (km), 34 cities of England and Wales pooled"); a.set_ylabel("Share of homes (%)")
a.set_xticks(range(0, 21, 2))
lg = a.legend(loc="upper left", bbox_to_anchor=(1.01, 1.0), fontsize=9.5, frameon=False, reverse=True)
a.set_title("Tree rings: homes of each era by distance from the centre", loc="left", fontproperties=DISPB, fontsize=13, color=FG)
fig.tight_layout()
savefig(fig, "rings", blog="rings", img="rings")

# ---------------------------------------------------------------- 4. cohort mean distance by period (tree rings, reversed at the end)
fig, a = plt.subplots(figsize=(11, 5.2), facecolor=PAPER)
for cty, t in PR.groupby("city"):
    t = t.sort_values("pidx")
    a.plot(t.pidx, t.rel, color="#B9B4A8", lw=0.8, alpha=0.8, zorder=1)
pm = pd.DataFrame(R["profile_mean_rel"])
a.plot(pm.pidx, pm["mean"], color=FG, lw=2.6, zorder=3, label="mean of the 34 cities")
a.scatter(pm.pidx, pm["mean"], c=PCOL, s=70, zorder=4, edgecolors="white", lw=1)
lt = PR[PR.city == "London"].sort_values("pidx")
a.plot(lt.pidx, lt.rel, color=HOT, lw=1.8, zorder=2, label="London")
a.axhline(1, color=MUT, lw=0.8, ls=":")
a.set_xticks(range(12)); a.set_xticklabels(PER_SHORT, rotation=45, ha="right", fontsize=9)
a.set_ylabel("Mean distance of the period's homes from the\ncentre, relative to all homes (1 = average)")
a.legend(handles=[Line2D([0], [0], color=FG, lw=2.6, label="mean of the 34 cities"), Line2D([0], [0], color=HOT, lw=1.8, label="London"),
                  Line2D([0], [0], color="#B9B4A8", lw=0.8, label="each city")], loc="upper left", fontsize=9.5, frameon=False)
style_axes(a)
a.set_title("Each era built farther out, until the 1990s; then the new homes came back in", loc="left", fontproperties=DISPB, fontsize=13, color=FG)
fig.tight_layout()
savefig(fig, "cohort", blog="cohort", img="cohort")

# ---------------------------------------------------------------- 5. six city profiles (pre-1919, interwar, post-war, 2009+ by band)
cities6 = ["London", "Birmingham", "Manchester", "Leeds", "Bristol", "Cardiff"]
fig, axs = plt.subplots(2, 3, figsize=(12, 6.6), facecolor=PAPER, sharex=True, sharey=True)
for a, cty in zip(axs.ravel(), cities6):
    t = CB[(CB.city == cty) & (CB.homes >= 1000)].sort_values("bin")
    for g in ("pre1919", "interwar", "postwar", "new"):
        a.plot(t.bin + 0.5, t[g] * 100, color=GCOL[g] if g != "postwar" else "#C9A04A", lw=2.2, label=GROUP_LABEL[g])
    a.set_title(cty, loc="left", fontproperties=DISPB, fontsize=12.5, color=FG)
    style_axes(a); a.set_xlim(0, 20); a.set_ylim(0, 75)
for a in axs[1]:
    a.set_xlabel("km from the centre")
for a in axs[:, 0]:
    a.set_ylabel("Share of homes (%)")
fig.legend(*axs[0, 0].get_legend_handles_labels(), loc="upper center", ncol=4, fontsize=9.5, frameon=False, bbox_to_anchor=(0.5, 1.0))
fig.tight_layout(rect=(0, 0, 1, 0.95))
savefig(fig, "cities", blog="cities", img="cities")

# ---------------------------------------------------------------- 6. local authorities: pre-1919 against 2009 onwards
fig, a = plt.subplots(figsize=(11, 6.4), facecolor=PAPER)
a.scatter(LA.pre1919, LA.new, s=np.sqrt(LA.homes) / 3, c=[PCOL[int(k)] for k in LA.median_idx], edgecolors="white", lw=0.5, alpha=0.95)
lab = set([r["name"] for r in R["la_oldest_pre1919"][:4]] + [r["name"] for r in R["la_newest"][:4]] + [r["name"] for r in R["la_youngest_pre1919"][:3]])
offs = {}
for code, r in LA.iterrows():
    if r["name"] in lab:
        dx, dy = (6, 4)
        a.annotate(r["name"], (r.pre1919, r.new), xytext=(dx, dy), textcoords="offset points", fontsize=9, color=FG,
                   bbox=dict(boxstyle="round,pad=0.15", fc=PAPER, ec="none", alpha=0.85))
a.set_xlabel("Homes built before 1919 (%)"); a.set_ylabel("Homes built 2009 onwards (%)")
style_axes(a)
h = [Line2D([0], [0], marker="o", color="none", markerfacecolor=PCOL[k], markeredgecolor="white", markersize=9, label=PER_LABEL[k]) for k in sorted(LA.median_idx.unique())]
a.legend(handles=h, title="Median home built", loc="upper right", ncol=2, fontsize=9, title_fontsize=9.5, frameon=False)
a.set_title(f"The {R['n_la']} local authorities: old stock or new building", loc="left", fontproperties=DISPB, fontsize=13, color=FG)
fig.tight_layout()
savefig(fig, "la", blog="la", img="la")

# ---------------------------------------------------------------- 7. Council Tax band by period (England)
B = R["bands"]["England"]
fig, a = plt.subplots(figsize=(11, 4.6), facecolor=PAPER)
ab = [B[p]["AB"] for p in PER]; fgh = [B[p]["FGH"] for p in PER]
xx = np.arange(12)
a.bar(xx - 0.2, ab, 0.4, color="#8FA7B8", label="Bands A and B (lowest)")
a.bar(xx + 0.2, fgh, 0.4, color="#7A2E1C", label="Bands F, G and H (highest)")
a.set_xticks(xx); a.set_xticklabels(PER_SHORT, rotation=45, ha="right", fontsize=9)
a.set_ylabel("Share of the period's homes (%)"); style_axes(a); a.legend(frameon=False, fontsize=9.5)
a.set_title("Council Tax band by build period, England (bands reflect 1991 values)", loc="left", fontproperties=DISPB, fontsize=13, color=FG)
fig.tight_layout()
savefig(fig, "bands", blog="bands", img="bands")

# ---------------------------------------------------------------- 8. robustness (paper)
rb = R["robust"]; mn = R["main"]
specs = [("Main", mn), ("Suppressed cells = 2.5", rb["dash"]), ("Pre-1900 = 1850", rb["pre1850"]), ("Pre-1900 = 1890", rb["pre1890"]),
         ("Catchment 10 km", rb["catch10"]), ("Catchment 30 km", rb["catch30"]), ("Natural Earth centres", rb["ne_centres"]),
         ("Unknown share < 2%", rb["unknown2"]), ("Without London", rb["no_london"])]
fig, axs = plt.subplots(1, 3, figsize=(12, 4.6), facecolor=PAPER, sharey=True)
yy = np.arange(len(specs))[::-1]
for k, (key, lo, hi, lab, scale) in enumerate([("m1_b", "m1_lo", "m1_hi", "M1: years per km", 1), ("m2_b", "m2_lo", "m2_hi", "M2: % farther per period", 100),
                                               (None, None, None, "M3: 2009+ vs 1983-99, % distance", 100)]):
    a = axs[k]
    for y_, (nm, s) in zip(yy, specs):
        if key:
            b, l, h = s[key], s[lo], s[hi]
            if k == 1:
                b, l, h = [(np.exp(v) - 1) * 100 for v in (b, l, h)]
        else:
            b, l, h = s["m3"]["pct_change"], s["m3"]["pct_lo"], s["m3"]["pct_hi"]
        a.plot([l, h], [y_, y_], color=FG, lw=1.4); a.plot([b], [y_], "o", color=HOT if nm == "Main" else FG, ms=6)
    a.axvline(0, color=MUT, lw=0.8, ls=":")
    if k == 0:
        a.axvline(R["placebo"]["m1_p95"], color=HOT, lw=1, ls="--"); a.text(R["placebo"]["m1_p95"], len(specs) - 0.4, " placebo 95th pct", color=HOT, fontsize=8)
    if k == 1:
        v = (np.exp(R["placebo"]["m2_p95"]) - 1) * 100
        a.axvline(v, color=HOT, lw=1, ls="--"); a.text(v, len(specs) - 0.4, " placebo 95th pct", color=HOT, fontsize=8)
    a.set_title(lab, loc="left", fontsize=10.5, color=FG); style_axes(a); a.grid(False)
axs[0].set_yticks(yy); axs[0].set_yticklabels([s[0] for s in specs], fontsize=9)
fig.tight_layout()
savefig(fig, "robust")

# ---------------------------------------------------------------- 9. M1 distance bins (paper)
bins = pd.DataFrame(R["m1_bins"])
fig, a = plt.subplots(figsize=(10, 4), facecolor=PAPER)
a.errorbar(bins.bin + 0.5, bins.b, yerr=[bins.b - bins.lo, bins.hi - bins.b], fmt="o", color=FG, ms=5, capsize=2, lw=1)
a.axhline(0, color=MUT, lw=0.8, ls=":")
a.set_xlabel("Distance from the centre (km, 1 km bands)"); a.set_ylabel("Mean build year relative\nto the 0 to 1 km band (years)")
style_axes(a)
a.set_title("Mean build year by distance band, city fixed effects (95% CI, LAD clusters)", loc="left", fontproperties=DISPB, fontsize=12.5, color=FG)
fig.tight_layout()
savefig(fig, "bins")
print("figures done")

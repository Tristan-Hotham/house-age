"""Reddit collage (r/dataisbeautiful style, light background): the LSOA map of England and Wales by median build period,
two city close-ups and the tree-ring chart. Reads data/lsoa_measures.csv, data/city_periods.csv, data/cities.csv and
data/results.json. Run from the study root: python3 reddit/collage.py"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "code"))
import pandas as pd
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
from figstyle import *

R = jload(f"{DATA}/results.json")
X = pd.read_csv(f"{DATA}/lsoa_measures.csv", index_col="lsoa21cd")
CT = pd.read_csv(f"{DATA}/cities.csv")
PR = pd.read_csv(f"{DATA}/city_periods.csv")
G = lsoa_shapes().join(X[["median_period"]])
G["col"] = G.median_period.map({l: PCOL[k] for k, l in enumerate(PER_LABEL)}).fillna(NODATA)
N = R["nat"]["England and Wales"]; M = R["main"]
fig = plt.figure(figsize=(16, 13.5), facecolor=PAPER)
fig.text(0.03, 0.972, "How old is your neighbourhood? Every small area of England and Wales", fontproperties=DISP, fontsize=31, color=FG, va="top")
fig.text(0.03, 0.93, f"The {R['meta']['n_lsoa']:,} small areas (760 homes on average) coloured by the build period of their median home. "
         f"{N['pre1919']:.0f}% of homes predate 1919; {N['new']:.0f}% were built since 2009.", fontproperties=SERP, fontsize=15.5, color=MUT, va="top")
ax = fig.add_axes([0.0, 0.07, 0.56, 0.835])
context_land(ax, (130000, 660000, 5000, 660000))
draw_polys(ax, G.geometry, G.col)
h = [Patch(facecolor=c, label=l) for c, l in zip(PCOL, PER_LABEL)]
lg = fig.legend(handles=h, loc="upper left", bbox_to_anchor=(0.572, 0.508), ncol=4, fontsize=10.5, title="Map colours: build period of the median home",
                title_fontsize=12, frameon=False, alignment="left", columnspacing=1.2, handlelength=1.6)
for k, (city, half) in enumerate([("London", 17000), ("Manchester", 12000)]):
    a = fig.add_axes([0.575 + k * 0.205, 0.585, 0.195, 0.29])
    c = CT[CT.city == city].iloc[0]; e = (c.x - half, c.x + half, c.y - half, c.y + half)
    context_land(a, e)
    s = G.cx[e[0] - 2000:e[1] + 2000, e[2] - 2000:e[3] + 2000]
    draw_polys(a, s.geometry, s.col)
    a.plot([c.x], [c.y], marker="+", ms=13, mew=2.4, color=FG, zorder=5)
    a.set_title(f"{city}: + is the centre", loc="left", fontproperties=DISPB, fontsize=14, color=FG, pad=4)
    for s_ in a.spines.values():
        s_.set_visible(True); s_.set_color(RULE)
fig.text(0.575, 0.572, f"Blue at the centre: within 1 km of the 34 city centres,\n{R['pooled_first']['new']:.0f}% of homes were built in 2009 or later.\nThe oldest homes form a ring 1 to 2 km out.", fontsize=11.5, color=FG, va="top")
a = fig.add_axes([0.62, 0.115, 0.355, 0.245])
for cty, t in PR.groupby("city"):
    t = t.sort_values("pidx"); a.plot(t.pidx, t.rel, color="#C9C4B8", lw=0.8, zorder=1)
pm = pd.DataFrame(R["profile_mean_rel"])
a.plot(pm.pidx, pm["mean"], color=FG, lw=2.8, zorder=3)
a.scatter(pm.pidx, pm["mean"], c=PCOL, s=90, zorder=4, edgecolors="white", lw=1.2)
a.axhline(1, color=MUT, lw=0.8, ls=":")
a.set_xticks(range(12)); a.set_xticklabels(PER_SHORT, rotation=45, ha="right", fontsize=10)
a.set_ylabel("distance from centre\n(1 = average home)", fontsize=11); style_axes(a); a.set_facecolor(PAPER); a.set_ylim(0.38, 1.38)
a.set_title("Cities grow in rings, then the new homes came back in", loc="left", fontproperties=DISPB, fontsize=15, color=FG, pad=40)
a.text(0, 1.03, f"Up to 1972, each era stands {M['m2_pct']:.1f}% farther out than the last;\nhomes built since 2009 stand {abs(M['m3']['pct_change']):.0f}% closer in than those of 1983 to 1999", transform=a.transAxes, fontsize=10.2, color=MUT)
a.legend(handles=[Line2D([0], [0], color=FG, lw=2.8, label="average of 34 cities"), Line2D([0], [0], color="#C9C4B8", lw=1, label="each city")], loc="lower right", fontsize=10, frameon=False)
fig.text(0.03, 0.042, "Data: Valuation Office Agency, Council Tax stock of properties at 31 March 2025 (OGL); ONS LSOA 2021 boundaries (OGL); cities: Natural Earth, Wikidata",
         fontsize=10.5, color=MUT)
fig.text(0.03, 0.016, "Dr Tristan Hotham  ·  maps.tristanhotham.com/house-age", fontsize=11.5, color=FG)
out = os.path.join(ROOT, "reddit", "house_age_collage.png")
fig.savefig(out, dpi=170, facecolor=PAPER)
print(out)

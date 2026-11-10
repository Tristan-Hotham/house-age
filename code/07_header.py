"""Step 7: header.png, the 1200 x 630 social card: title and two numbers on light paper beside the LSOA map."""
import pandas as pd
from PIL import Image
from figstyle import *

R = jload(f"{DATA}/results.json")
X = pd.read_csv(f"{DATA}/lsoa_measures.csv", index_col="lsoa21cd")
G = lsoa_shapes().join(X[["median_period"]])
G["col"] = G.median_period.map({l: PCOL[k] for k, l in enumerate(PER_LABEL)}).fillna(NODATA)
fig = plt.figure(figsize=(12, 6.3), dpi=100, facecolor=PAPER)
ax = fig.add_axes([0.52, 0.0, 0.48, 1.0])
context_land(ax, (150000, 660000, 5000, 660000))
draw_polys(ax, G.geometry, G.col)
N = R["nat"]["England and Wales"]
fig.text(0.045, 0.86, "How old is your", fontproperties=DISP, fontsize=46, color=FG, va="top")
fig.text(0.045, 0.73, "neighbourhood?", fontproperties=DISP, fontsize=46, color=HOT, va="top")
fig.text(0.045, 0.58, f"Every small area of England and Wales by the age\nof its homes, from the Council Tax lists of 2025", fontproperties=SERP, fontsize=17, color=MUT, va="top", linespacing=1.3)
fig.text(0.045, 0.40, f"{N['pre1919']:.0f}%", fontproperties=DISP, fontsize=40, color=PCOL[1], va="top")
fig.text(0.155, 0.385, "of homes built\nbefore 1919", fontsize=13, color=FG, va="top")
fig.text(0.315, 0.40, f"{N["new"]:.0f}%", fontproperties=DISP, fontsize=40, color=PCOL[-1], va="top")
fig.text(0.425, 0.385, "since\n2009", fontsize=13, color=FG, va="top")
for k, c in enumerate(PCOL):
    fig.patches.append(plt.Rectangle((0.045 + k * 0.034, 0.17), 0.034, 0.035, transform=fig.transFigure, facecolor=c, edgecolor="none"))
fig.text(0.045, 0.15, "before 1900", fontsize=11, color=MUT, va="top"); fig.text(0.453, 0.15, "2009 on", fontsize=11, color=MUT, va="top", ha="right")
fig.text(0.045, 0.05, "Dr Tristan Hotham  ·  maps.tristanhotham.com/house-age", fontsize=11.5, color=MUT)
fig.savefig(f"{ROOT}/header.png", dpi=100, facecolor=PAPER)
assert Image.open(f"{ROOT}/header.png").size == (1200, 630)
print("header.png")

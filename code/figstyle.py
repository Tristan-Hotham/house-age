"""House style for the static figures: light paper, Fraunces titles, Source Serif and IBM Plex Mono text, and a twelve-step palette for
build periods from deep brown (before 1900) to deep blue (2009 onwards)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.colors import ListedColormap, BoundaryNorm
import numpy as np
from common import *

_FD = os.path.join(SCR, "fonts")
os.makedirs(_FD, exist_ok=True)
if not os.path.exists(f"{_FD}/Fraunces-Black.ttf"):
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer
    for w, nm in ((900, "Black"), (700, "Bold")):
        instancer.instantiateVariableFont(TTFont(f"{FONTS}/FrauncesVar.ttf"), {"wght": w, "opsz": 144, "SOFT": 0, "WONK": 0}).save(f"{_FD}/Fraunces-{nm}.ttf")
DISP = fm.FontProperties(fname=f"{_FD}/Fraunces-Black.ttf")
DISPB = fm.FontProperties(fname=f"{_FD}/Fraunces-Bold.ttf")
SERP = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-Regular.ttf")
SERI = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-It.ttf")
for f in ("IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
MONO = "IBM Plex Mono"
plt.rcParams.update({"font.family": MONO, "font.size": 11, "axes.edgecolor": "#636A72", "axes.labelcolor": "#1D2128",
                     "xtick.color": "#636A72", "ytick.color": "#636A72", "axes.unicode_minus": False, "pdf.fonttype": 42})
PAPER, FG, MUT, RULE = "#F6F4EF", "#1D2128", "#636A72", "#DDD8CC"
SEA, SAND, EDGE = "#E4ECF0", "#ECE8DF", "#B9AE98"
HOT = "#B3202A"
GCOL = {"pre1919": "#7A2E1C", "interwar": "#D27D3E", "postwar": "#E9C77F", "late20": "#8FC3B8", "early21": "#3E86A6", "new": "#1F3F78"}
NODATA = "#D9D6CF"


def period_cmap():
    return ListedColormap(PCOL), BoundaryNorm(np.arange(-0.5, 12.5, 1), 12)


def lsoa_shapes(tol=40):
    """LSOA polygons in British National Grid, simplified for drawing, cached in SCR (index LSOA21CD)."""
    import geopandas as gpd
    fn = os.path.join(SCR, f"lsoa_bng_s{tol}.gpkg")
    if not os.path.exists(fn):
        g = gpd.read_file(LSOA_GPKG)[["LSOA21CD", "geometry"]].to_crs(27700)
        g["geometry"] = g.geometry.simplify(tol, preserve_topology=True)
        g.to_file(fn)
    return gpd.read_file(fn).set_index("LSOA21CD")


def draw_polys(ax, geoms, colors, lw=0, ec="none", zorder=2, rasterized=True):
    from matplotlib.patches import Polygon as MPoly
    from matplotlib.collections import PatchCollection
    patches, cols = [], []
    for g, c in zip(geoms, colors):
        for p in (g.geoms if g.geom_type == "MultiPolygon" else [g]):
            patches.append(MPoly(np.asarray(p.exterior.coords), closed=True)); cols.append(c)
    pc = PatchCollection(patches, facecolor=cols, edgecolor=ec if lw else cols, linewidth=lw if lw else 0.15, zorder=zorder, rasterized=rasterized)
    ax.add_collection(pc)
    return pc


def context_land(ax, ext=None):
    """Neighbouring land (Scotland, Ireland, France, Isle of Man) in light grey, in BNG, on a sea background."""
    import geopandas as gpd
    fn = os.path.join(SCR, "context_bng.gpkg")
    if not os.path.exists(fn):
        c = gpd.read_file(os.path.join(GEO, "ne_10m_admin_0_countries.geojson"))
        c = c[c.ADM0_A3.isin(["IRL", "IMN", "FRA", "GBR"])].clip((-11, 48.5, 3, 61)).to_crs(27700)
        lad = gpd.read_file(os.path.join(GEO, "lad23_bgc.geojson")).to_crs(27700)
        cc = [k for k in lad.columns if k.upper().startswith("LAD") and k.upper().endswith("CD")][0]
        other = lad[~lad[cc].str[0].isin(["E", "W"])]
        g = gpd.GeoDataFrame(geometry=list(c[c.ADM0_A3 != "GBR"].geometry) + list(other.geometry), crs=27700)
        g["geometry"] = g.geometry.simplify(300)
        g.to_file(fn)
    g = gpd.read_file(fn)
    ax.set_facecolor(SEA)
    draw_polys(ax, g.geometry, ["#E9E6DF"] * len(g), lw=0.3, ec="#CFC8B8", zorder=1)
    if ext:
        ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3])
    ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
    for s_ in ax.spines.values():
        s_.set_visible(False)


def style_axes(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(axis="y", color=RULE, lw=0.6)
    ax.set_axisbelow(True)


def savefig(fig, stem, blog=None, img=None, pdf=True):
    """f_<stem>.pdf for the paper, release/blog/b_<blog>.png at 1800 px wide, img/<img>.jpg for the page"""
    os.makedirs(f"{REL}/paper", exist_ok=True); os.makedirs(f"{REL}/blog", exist_ok=True)
    if pdf:
        fig.savefig(f"{REL}/paper/f_{stem}.pdf", facecolor=fig.get_facecolor())
    w = fig.get_figwidth()
    if blog:
        fig.savefig(f"{REL}/blog/b_{blog}.png", dpi=1800 / w, facecolor=fig.get_facecolor())
    if img:
        tmp = f"{SCR}/_tmp.png"
        fig.savefig(tmp, dpi=1400 / w, facecolor=fig.get_facecolor())
        from PIL import Image
        Image.open(tmp).convert("RGB").save(f"{IMG}/{img}.jpg", quality=86, optimize=True)
        os.remove(tmp)
    plt.close(fig)

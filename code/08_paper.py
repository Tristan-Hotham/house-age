"""Step 8: the paper. Fills code/paper_template.tex with code/paper_body.tex and tables built here from data/results.json,
then compiles with xelatex. Output: release/paper/Hotham_House_Age.pdf and .tex beside the f_*.pdf figures.
The DOI stays a placeholder (https://doi.org/10.5281/zenodo.24113860 printed) unless DOI is set: DOI=10.5281/zenodo.N python3 code/08_paper.py"""
import subprocess
import numpy as np
from common import *

R = jload(f"{DATA}/results.json")
OUT = os.path.join(REL, "paper"); NAME = "Hotham_House_Age"
tex = lambda s: str(s).replace("\\", "").replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#").replace("$", "\\$")
neg = lambda s: s.replace("-", "$-$") if s.startswith("-") else s


def tf(v, f):
    s = fmt(v, f)
    s = s.replace("%", "\\%")
    return ("$-$" + s[1:]) if s.startswith("-") else s


N = R["nat"]
rows = ""
for p, lab in zip(PER, PER_LABEL):
    py = R["per_year"].get(p if p != "2009on" else "2009_2024")
    rows += f"{lab} & {N['England and Wales'][p]:.1f} & {N['England'][p]:.1f} & {N['Wales'][p]:.1f} & {N['England and Wales'][p] / 100 * N['England and Wales']['known']:,.0f} & {'' if py is None else f'{py:,.0f}'}\\\\\n"
rows += f"\\midrule Unknown (share of all) & {N['England and Wales']['unknown_share']:.2f} & {N['England']['unknown_share']:.2f} & {N['Wales']['unknown_share']:.2f} & {N['England and Wales']['unknown']:,.0f} & \\\\\n"
rows += f"Homes of known period & & & & {N['England and Wales']['known']:,.0f} & \\\\\n"
T_NAT = ("\\begin{table}[tbp]\\centering\\small\\caption{Homes on the Council Tax lists at 31 March 2025 by build period: share of homes of known period (\\%), number (England and Wales) and surviving homes per year of the period (for 2009 onwards: per year, 2009 to 2024). Source: VOA CTSOP4.1.}\\label{tab:national}"
         "\\begin{tabular}{lrrrrr}\\toprule Build period & England and Wales & England & Wales & Homes & Per year\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")

rows = "".join(f"{tex(nm)} & {g['pre1919']:.1f} & {g['interwar']:.1f} & {g['postwar']:.1f} & {g['late20']:.1f} & {g['early21']:.1f} & {g['new']:.1f} & {g['mean_year']:.0f}\\\\\n" for nm, g in R["regions"].items())
T_REG = ("\\begin{table}[tbp]\\centering\\small\\caption{Homes by build era and region (share of homes of known period, \\%; LSOAs assigned to regions by the ONS boundary file) and the mean build year.}\\label{tab:regions}"
         "\\begin{tabular}{lrrrrrrr}\\toprule Region & Pre-1919 & 1919 to 39 & 1945 to 72 & 1973 to 99 & 2000 to 08 & 2009 on & Mean year\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")


def la_rows(lst):
    return "".join(f"\\quad {tex(r['name'])} & {r['homes']:,.0f} & {r['pre1919']:.1f} & {r['new']:.1f} & {tex(r['median'])}\\\\\n" for r in lst)
T_LA = ("\\begin{table}[tbp]\\centering\\small\\caption{Local authorities with the highest and lowest share of homes built before 1919, and the highest share built from 2009 onwards (shares of homes of known period, \\%). Source: VOA CTSOP4.1 (local authority rows).}\\label{tab:la}"
        "\\begin{tabular}{lrrrl}\\toprule Local authority & Homes & Before 1919 & 2009 on & Median home\\\\\\midrule\n"
        "\\multicolumn{5}{l}{\\textit{Highest share before 1919}}\\\\\n" + la_rows(R["la_oldest_pre1919"]) +
        "\\multicolumn{5}{l}{\\textit{Lowest share before 1919}}\\\\\n" + la_rows(R["la_youngest_pre1919"][:5]) +
        "\\multicolumn{5}{l}{\\textit{Highest share from 2009 onwards}}\\\\\n" + la_rows(R["la_newest"]) + "\\bottomrule\\end{tabular}\\end{table}")

B = R["bands"]
rows = "".join(f"{lab} & {B['England'][p]['AB']:.1f} & {B['England'][p]['FGH']:.1f} & {B['England'][p]['mean_band']:.2f} & {B['Wales'][p]['AB']:.1f} & {B['Wales'][p]['FGH']:.1f} & {B['Wales'][p]['mean_band']:.2f}\\\\\n" for p, lab in zip(PER, PER_LABEL))
T_BANDS = ("\\begin{table}[tbp]\\centering\\small\\caption{Council Tax band by build period: share of the period's homes in bands A and B, in the top bands (England F to H; Wales F to I) and the mean band (A = 1). England's bands rest on 1991 values and Wales's on 2003 values, so the two are not comparable.}\\label{tab:bands}"
           "\\begin{tabular}{lrrrrrr}\\toprule & \\multicolumn{3}{c}{England} & \\multicolumn{3}{c}{Wales}\\\\\\cmidrule(lr){2-4}\\cmidrule(lr){5-7} Build period & A, B (\\%) & F to H (\\%) & Mean & A, B (\\%) & F to I (\\%) & Mean\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")

m = R["main"]
T_MOD = ("\\begin{table}[tbp]\\centering\\small\\caption{Main pre-specified estimates. M1: weighted least squares of LSOA mean build year on distance (km) with city fixed effects, weights = homes of known period, SE clustered by local authority. M2: OLS of log mean distance of each period's homes on period order (before 1900 = 0 to 1965 to 1972 = 6), city fixed effects, SE clustered by city. M3: mean over cities of the log difference in mean distance between homes built 2009 onwards and 1983 to 1999, $t$ interval. Placebo: centres moved 10 km in a random direction, 200 draws.}\\label{tab:models}"
         "\\setlength{\\tabcolsep}{4pt}\\begin{tabular}{lrrrl}\\toprule Model & Estimate & 95\\% CI & $N$ & Placebo p95\\\\\\midrule\n"
         f"M1 (years per km) & {tf(m['m1_b'], 'f3')} & [{tf(m['m1_lo'], 'f3')}, {tf(m['m1_hi'], 'f3')}] & {m['n_lsoa']:,} LSOAs, {m['n_lad']} clusters & {tf(R['placebo']['m1_p95'], 'f3')} (fails)\\\\\n"
         f"\\quad clustered by city & & [{tf(R['m1_cluster_city']['lo'], 'f3')}, {tf(R['m1_cluster_city']['hi'], 'f3')}] & {m['n_city']} clusters & \\\\\n"
         f"M2 (log distance per period) & {tf(m['m2_b'], 'f3')} & [{tf(m['m2_lo'], 'f3')}, {tf(m['m2_hi'], 'f3')}] & {m['m2_n']} cells, {m['n_city']} clusters & {tf(R['placebo']['m2_p95'], 'f3')} (passes)\\\\\n"
         f"\\quad cities with positive Spearman $\\rho$ & {m['m2_rho_pos']} of {m['m2_rho_n']} & & & \\\\\n"
         f"M3 (log difference) & {tf(m['m3']['mean'], 'f3')} & [{tf(m['m3']['lo'], 'f3')}, {tf(m['m3']['hi'], 'f3')}] & {m['m3']['n']} cities & \\\\\n"
         f"\\quad cities with a negative difference & {m['m3']['neg']} of {m['m3']['n']} & & & \\\\\n"
         f"M1 quadratic: distance & {tf(R['m1_quad']['b1'], 'f3')} & & & \\\\\n"
         f"\\quad distance squared & {tf(R['m1_quad']['b2'], 'f4' if False else 'f3')} & $p$ = {R['m1_quad']['p2']:.3f} & & \\\\\n"
         "\\bottomrule\\end{tabular}\\end{table}")

rb = R["robust"]
specs = [("Main specification", m), ("R1 suppressed cells = 2.5", rb["dash"]), ("R2 pre-1900 midpoint 1850", rb["pre1850"]), ("R2 pre-1900 midpoint 1890", rb["pre1890"]),
         ("R3 catchment 10 km", rb["catch10"]), ("R3 catchment 30 km", rb["catch30"]), ("R4 Natural Earth centres", rb["ne_centres"]),
         ("R5 without London", rb["no_london"]), ("R7 unknown share below 2\\%", rb["unknown2"])]
rows = ""
for lab, s in specs:
    rows += (f"{lab} & {s['n_lsoa']:,} & {tf(s['m1_b'], 'f2')} [{tf(s['m1_lo'], 'f2')}, {tf(s['m1_hi'], 'f2')}] & {tf(s['m2_b'], 'f3')} [{tf(s['m2_lo'], 'f3')}, {tf(s['m2_hi'], 'f3')}] & "
             f"{tf(s['m3']['mean'], 'f3')} [{tf(s['m3']['lo'], 'f3')}, {tf(s['m3']['hi'], 'f3')}]\\\\\n")
rows += "\\midrule\\multicolumn{5}{l}{\\textit{R5 leaving out one region}}\\\\\n"
lo_ = rb["loro"]
for nm, s in lo_.items():
    rows += f"\\quad without {tex(nm)} & {s['n_lsoa']:,} & {tf(s['m1_b'], 'f2')} [{tf(s['m1_lo'], 'f2')}, {tf(s['m1_hi'], 'f2')}] & {tf(s['m2_b'], 'f3')} [{tf(s['m2_lo'], 'f3')}, {tf(s['m2_hi'], 'f3')}] & {tf(s['m3'], 'f3')} [{tf(s['m3_lo'], 'f3')}, {tf(s['m3_hi'], 'f3')}]\\\\\n"
ms = R["msoa"]
rows += f"\\midrule R8 MSOA level & {ms['n']:,} MSOAs & {tf(ms['m1_b'], 'f2')} [{tf(ms['m1_lo'], 'f2')}, {tf(ms['m1_hi'], 'f2')}] & {tf(ms['m2_b'], 'f3')} & \\\\\n"
pl = R["placebo"]
rows += f"R6 placebo centres, mean (95th pct) & 200 draws & {tf(pl['m1_mean'], 'f2')} ({tf(pl['m1_p95'], 'f2')}) & {tf(pl['m2_mean'], 'f3')} ({tf(pl['m2_p95'], 'f3')}) & \\\\\n"
T_ROB = ("\\begin{table}[tbp]\\centering\\footnotesize\\setlength{\\tabcolsep}{4pt}\\caption{Planned robustness checks: estimates and 95\\% intervals for M1 (years per km), M2 (log distance per period) and M3 (log difference, 2009 onwards against 1983 to 1999). R8 MSOA: M1 with SE clustered by city.}\\label{tab:robust}"
         "\\begin{tabular}{lrlll}\\toprule Check & LSOAs & M1 & M2 & M3\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
LORO = {"LORO_M2_MIN": min(s["m2_b"] for s in lo_.values()), "LORO_M2_MAX": max(s["m2_b"] for s in lo_.values()),
        "LORO_M3_MIN": min(s["m3"] for s in lo_.values()), "LORO_M3_MAX": max(s["m3"] for s in lo_.values())}
assert all(s["m2_lo"] > 0 and s["m3_hi"] < 0 for s in lo_.values())
assert all(s["m2_lo"] > 0 and s["m3"]["hi"] < 0 for _, s in specs)

rows = ""
for r in R["city_table"]:
    rows += (f"{tex(r['city'])} & {r['n_lsoa']:,} & {r['homes']:,.0f} & {r['pre1919']:.1f} & {r['new']:.1f} & {tf(r['rho'], 'f2')} & {tf(r['m3_pct'], 'f1')} & "
             f"{r['peak_pre1919']} / {r['peak_interwar']} / {r['peak_5572']} & {'yes' if r['order'] else 'no'}\\\\\n")
T_CIT = ("\\begin{table}[tbp]\\centering\\footnotesize\\setlength{\\tabcolsep}{4pt}\\caption{The " + str(m["n_city"]) + " cities: LSOAs and homes of known period within 20 km of the centre (nearest centre), shares built before 1919 and from 2009 (\\%), Spearman correlation of period order with mean distance (before 1900 to 1965 to 1972), the M3 difference in mean distance (2009 onwards against 1983 to 1999, \\%), and the inner edge (km) of the 1 km band with the highest pre-1919, interwar and 1955 to 1972 share, with whether the H4 order holds.}\\label{tab:citylist}\\label{tab:cities}"
         "\\begin{tabular}{lrrrrrrll}\\toprule City & LSOAs & Homes & Pre-1919 & 2009 on & $\\rho$ & M3 (\\%) & Peaks (km) & H4\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
pb = R["pooled_bands"]; bins = R["m1_bins"]
rows = "".join(f"{b['bin']} to {b['bin'] + 1} & {pb[k]['homes']:,.0f} & {pb[k]['mean_year']:.1f} & {tf(b['b'], 'f1')} & [{tf(b['lo'], 'f1')}, {tf(b['hi'], 'f1')}] & {pb[k]['pre1919'] * 100:.1f} & {pb[k]['interwar'] * 100:.1f} & {pb[k]['postwar'] * 100:.1f} & {pb[k]['new'] * 100:.1f}\\\\\n" for k, b in enumerate(bins))
T_BINS = ("\\begin{table}[tbp]\\centering\\footnotesize\\setlength{\\tabcolsep}{4pt}\\caption{Distance bands (km), all cities pooled: homes of known period, mean build year, the M1 bin coefficient relative to 0 to 1 km (city fixed effects, 95\\% CI with SE clustered by local authority) and the shares (\\%) built before 1919, between the wars, 1945 to 1972 and from 2009.}\\label{tab:bins}"
          "\\begin{tabular}{lrrrlrrrr}\\toprule Band & Homes & Mean year & Coefficient & 95\\% CI & Pre-1919 & Interwar & Post-war & 2009 on\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")

t = open(os.path.join(CODE, "paper_template.tex"), encoding="utf-8").read()
t = t.replace("%%BODY%%", open(os.path.join(CODE, "paper_body.tex"), encoding="utf-8").read())
for k, v in (("TABLE_NATIONAL", T_NAT), ("TABLE_REGIONS", T_REG), ("TABLE_LA", T_LA), ("TABLE_BANDS", T_BANDS), ("TABLE_MODELS", T_MOD), ("TABLE_ROBUST", T_ROB),
             ("TABLE_CITIES", T_CIT), ("TABLE_BINS", T_BINS)):
    t = t.replace("{{" + k + "}}", v)
t = t.replace("{{AI}}", AI)
doi = os.environ.get("DOI")
t = t.replace("https://doi.org/10.5281/zenodo.24113860", f"https://doi.org/{doi}" if doi else "\\{\\{DOI\\_URL\\}\\}")


def fill(mm):
    k, f = mm.group(1), mm.group(3)
    if k in LORO: return tf(LORO[k], f)
    return tf(get(R, k), f) if f else tex(get(R, k))


t = re.sub(r"\{\{([^{}|]+)(\|(\w+))?\}\}", fill, t)
assert "{{" not in t.replace("\\{\\{DOI\\_URL\\}\\}", ""), re.findall(r"\{\{[^}]*\}\}", t)[:5]
vis = re.sub(r"%.*", "", t)
for bad in ("\u2014", "\u2013", "--", "DSIT", "DCMS", "civil serv", "pre-registered"):
    assert bad not in vis, bad
assert AI in t
os.makedirs(OUT, exist_ok=True)
open(f"{OUT}/{NAME}.tex", "w", encoding="utf-8").write(t)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", f"{NAME}.tex"], cwd=OUT, capture_output=True, text=True)
log = open(f"{OUT}/{NAME}.log", encoding="utf-8", errors="ignore").read()
assert os.path.exists(f"{OUT}/{NAME}.pdf"), r.stdout[-3000:]
und = re.findall(r"(?:Citation|Reference) `([^']+)' .*undefined", log)
assert not und, und
for ext in ("aux", "log", "out"):
    if os.path.exists(f"{OUT}/{NAME}.{ext}"):
        os.remove(f"{OUT}/{NAME}.{ext}")
# word count of the body text (before references)
body = re.sub(r"\\begin\{table\}.*?\\end\{table\}|\\begin\{figure\}.*?\\end\{figure\}", " ", t, flags=re.S)
main = body.split("\\begin{thebibliography}")[0].split("\\begin{document}")[1]
words = len(re.sub(r"\\[a-zA-Z]+\*?(\[[^]]*\])?|[{}$\\]", " ", main).split())
ab = re.search(r"\\textbf\{Abstract\}\\end\{center\}\n(.*?)\n\n", t, re.S).group(1)
abw = len(re.sub(r"\\[a-zA-Z]+|[{}$\\]", " ", ab).split())
pages = subprocess.run(["pdfinfo", f"{OUT}/{NAME}.pdf"], capture_output=True, text=True).stdout
print("paper", NAME, "words", words, "abstract words", abw, re.search(r"Pages:\s+\d+", pages).group(0))

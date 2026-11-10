"""Step 11: README.md from data/results.json."""
from common import *

R = jload(f"{DATA}/results.json")
N = R["nat"]["England and Wales"]; M = R["main"]; P = R["placebo"]
rows = "\n".join(f"| {lab} | {N[p]:.1f}% | {R['nat']['England'][p]:.1f}% | {R['nat']['Wales'][p]:.1f}% |" for p, lab in zip(PER, PER_LABEL))
t = f"""# How old is your neighbourhood?

The age of the homes in every small area of England and Wales, and the tree rings of its cities. Every one of the {R['meta']['n_lsoa']:,} lower layer super output areas (LSOAs, 2021) mapped by the build period of its homes, from the Valuation Office Agency's count of every property on the Council Tax lists at 31 March 2025, with a pre-specified test of whether the {M['n_city']} cities of England and Wales hold their housing in rings of age. A data study by Dr Tristan Hotham (Independent researcher). The analysis was pre-specified in a written plan before any distance was computed (NOTES.md).

Interactive page: https://maps.tristanhotham.com/house-age/
Paper: {{https://doi.org/10.5281/zenodo.24113860}}
Blog post: {{https://blog.tristanhotham.com/2026/10/31/house-age/}}
Code and data: {REPO}

## Headline results

| Build period | England and Wales | England | Wales |
|---|---|---|---|
{rows}

- {N['pre1919']:.1f}% of homes with a known build period predate 1919, {N['postwar']:.1f}% date from 1945 to 1972 and {N['new']:.1f}% from 2009 onwards ({N['unknown_share']:.2f}% of homes have no recorded period). The median home was built between 1955 and 1964.
- Oldest local authority: Kensington and Chelsea ({R['la_oldest_pre1919'][0]['pre1919']:.1f}% before 1919). Newest: {R['la_newest'][0]['name']} ({R['la_newest'][0]['new']:.1f}% from 2009). In {R['frontier_n']:,} LSOAs at least half the homes date from 2009 or later.
- Rings (H2): within 20 km of the {M['n_city']} city centres, each successive period's homes from before 1900 to 1965 to 1972 stand {M['m2_pct']:.1f}% farther out (95% CI {M['m2_pct_lo']:.1f} to {M['m2_pct_hi']:.1f}; positive in {M['m2_rho_pos']} of {M['m2_rho_n']} cities). Placebo centres moved 10 km at random never come close (95th percentile {P['m2_p95']:.3f} against {M['m2_b']:.3f} in logs).
- Reversal (H3): homes built from 2009 stand {abs(M['m3']['pct_change']):.1f}% closer to the centre than homes of 1983 to 1999 (95% CI {abs(M['m3']['pct_hi']):.1f} to {abs(M['m3']['pct_lo']):.1f}; closer in {M['m3']['neg']} of {M['m3']['n']} cities). Within 1 km of the centres, {R['pooled_first']['new']:.0f}% of homes date from 2009 or later.
- Interwar belt (H4): in {R['h4']['order']} of {R['h4']['n']} cities the interwar peak lies between the pre-1919 and the 1955 to 1972 peaks.
- Not supported (H1): the mean build year rises by {M['m1_b']:.2f} years per km, but placebo centres give a slope as steep in {P['m1_share_ge_real'] * 100:.1f}% of draws, so by the rule set in advance this gradient is not evidence of a centre-specific pattern.

## Files

| File | What it is |
|---|---|
| `index.html`, `js/page.js` | Interactive page: MapLibre on OpenFreeMap Positron; every LSOA coloured by median build period or by the share of homes in any period or era, play through the periods, popups with each area's full profile, search for towns, councils and LSOAs, layers, full screen. |
| `data/lsoa.topo.json`, `data/site_lsoa.json`, `data/site.json` | Page data: simplified LSOA polygons (mapshaper, 15% of vertices), per-LSOA shares, cities, councils and places. |
| `data/lsoa_age.csv`, `data/msoa_age.csv`, `data/la_age.csv` | VOA counts tidied: homes by build period (single years from 2009), unknown, Council Tax band and property type, for LSOAs, MSOAs and local authorities. |
| `data/lsoa_measures.csv` | Per LSOA: shares by period and era, median period, mean build year, unknown share, nearest city and distance. |
| `data/la_rank.csv` | Local authorities: shares by era, mean year, median period. |
| `data/nation_band_period.csv` | Council Tax band by build period for England and Wales, England and Wales separately. |
| `data/cities.csv` | The {M['n_city']} cities with Wikidata and Natural Earth centres. |
| `data/city_periods.csv`, `data/city_bands.csv` | Mean distance of each period's homes by city; era shares by 1 km band by city. |
| `data/models.csv`, `data/results.json` | Main model estimates; every number quoted anywhere. |
| `code/` | Scripts in order and templates. |
| `release/` | Paper (PDF, LaTeX, figures, cover note), blog post and figures, Zenodo files. |
| `reddit/` | Collage, its script, the post text and a looping GIF. |

## Method in brief

1. `00_boundaries.py`: ONS LSOA 2021 boundaries (generalised clipped) from the GitHub copy drkane/geo-lookups.
2. `01_prepare.py`: reads VOA tables CTSOP4.1 and CTSOP3.1; suppressed cells ("-", fewer than five) count as zero (2.5 as a check).
3. `02_cities.py`: cities = Natural Earth places in England and Wales with at least 100,000 people; centres from Wikidata.
4. `03_analysis.py`: shares, median period and mean build year per LSOA; each LSOA within 20 km assigned to its nearest centre; models M1 (mean year on distance, city fixed effects, local authority clusters), M2 (log mean distance of each period's homes on period order, city clusters), M3 (2009 onwards against 1983 to 1999), H4, nine robustness checks and the placebo (200 random 10 km moves of every centre).
5. `04_results.py` to `11_readme.py`: results, figures, header, page data, paper, page, release files and this README.

## Caveats

These are the homes standing in 2025, so demolished homes are missing and conversions can split one home into several properties. The build period is the VOA's age code: coarse before 1900, with no code for 1940 to 1944. Council Tax properties include annexes and some caravans and houseboats. Counts are rounded to the nearest 10. One centre per city and a 20 km circle simplify polycentric conurbations.

## Sources and licences

- Valuation Office Agency (2025) Council Tax: stock of properties, 2025, tables CTSOP3.1 and CTSOP4.1 (data at 31 March 2025). Official Statistics, Open Government Licence v3.0.
- Office for National Statistics, LSOA (December 2021) boundaries EW BGC, Open Government Licence v3.0 (contains OS data, Crown copyright and database right), via https://github.com/drkane/geo-lookups. MSOA 2021 and local authority boundaries from ONS (OGL).
- Natural Earth populated places (public domain); Wikidata (CC0). Base map: OpenFreeMap Positron, OpenStreetMap contributors (ODbL).
- This repository: code MIT; text, figures and derived data CC BY 4.0.

## How to rerun

Python 3 with numpy, pandas, geopandas, shapely, pyproj, statsmodels, scipy, matplotlib, rasterio and Pillow; mapshaper (npm) for the page geometry; xelatex for the paper. Put the VOA zips where `code/common.py` expects them (or set HA_VOA), then run `code/00_boundaries.py` to `code/11_readme.py` in order (`01_prepare.py` twice, the second time with `HA_DASH=2.5`) and `reddit/collage.py`. The paper's DOI line is filled from the environment: `DOI=10.5281/zenodo.N python3 code/08_paper.py`.

## Citation

Hotham, T. (2026) How old is your neighbourhood? The age of the housing stock in every small area of England and Wales, and the tree rings of its cities. Zenodo. {{https://doi.org/10.5281/zenodo.24113860}}

{AI}
"""
for bad in ("—", "–", "--", "DSIT", "DCMS", "pre-registered"):
    assert bad not in re.sub(r"\|[-|]+\|", "", t), bad
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(t)
print("README.md", len(t.split()), "words")

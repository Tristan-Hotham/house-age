# How old is your neighbourhood?

The age of the homes in every small area of England and Wales, and the tree rings of its cities. Every one of the 35,672 lower layer super output areas (LSOAs, 2021) mapped by the build period of its homes, from the Valuation Office Agency's count of every property on the Council Tax lists at 31 March 2025, with a pre-specified test of whether the 34 cities of England and Wales hold their housing in rings of age. A data study by Dr Tristan Hotham (Independent researcher). The analysis was pre-specified in a written plan before any distance was computed (NOTES.md).

Interactive page: https://maps.tristanhotham.com/house-age/
Paper: https://doi.org/10.5281/zenodo.24113860
Blog post: https://blog.tristanhotham.com/2026/10/31/house-age/
Code and data: https://github.com/Tristan-Hotham/house-age

## Headline results

| Build period | England and Wales | England | Wales |
|---|---|---|---|
| Before 1900 | 15.5% | 15.1% | 22.5% |
| 1900 to 1918 | 5.2% | 5.1% | 7.7% |
| 1919 to 1929 | 4.8% | 4.8% | 4.5% |
| 1930 to 1939 | 9.9% | 10.1% | 5.1% |
| 1945 to 1954 | 6.4% | 6.4% | 6.6% |
| 1955 to 1964 | 9.8% | 9.8% | 9.4% |
| 1965 to 1972 | 9.4% | 9.4% | 9.2% |
| 1973 to 1982 | 8.9% | 8.9% | 8.6% |
| 1983 to 1992 | 6.9% | 6.9% | 6.4% |
| 1993 to 1999 | 5.0% | 5.0% | 5.4% |
| 2000 to 2008 | 6.4% | 6.4% | 6.3% |
| 2009 onwards | 11.8% | 11.9% | 8.5% |

- 20.8% of homes with a known build period predate 1919, 25.7% date from 1945 to 1972 and 11.8% from 2009 onwards (0.75% of homes have no recorded period). The median home was built between 1955 and 1964.
- Oldest local authority: Kensington and Chelsea (65.7% before 1919). Newest: Tower Hamlets (31.7% from 2009). In 1,032 LSOAs at least half the homes date from 2009 or later.
- Rings (H2): within 20 km of the 34 city centres, each successive period's homes from before 1900 to 1965 to 1972 stand 4.3% farther out (95% CI 3.1 to 5.5; positive in 33 of 34 cities). Placebo centres moved 10 km at random never come close (95th percentile 0.010 against 0.042 in logs).
- Reversal (H3): homes built from 2009 stand 9.0% closer to the centre than homes of 1983 to 1999 (95% CI 4.9 to 13.0; closer in 26 of 34 cities). Within 1 km of the centres, 32% of homes date from 2009 or later.
- Interwar belt (H4): in 32 of 34 cities the interwar peak lies between the pre-1919 and the 1955 to 1972 peaks.
- Not supported (H1): the mean build year rises by 0.61 years per km, but placebo centres give a slope as steep in 8.5% of draws, so by the rule set in advance this gradient is not evidence of a centre-specific pattern.

## Files

| File | What it is |
|---|---|
| `index.html`, `js/page.js` | Interactive page: MapLibre on OpenFreeMap Positron; every LSOA coloured by median build period or by the share of homes in any period or era, play through the periods, popups with each area's full profile, search for towns, councils and LSOAs, layers, full screen. |
| `data/lsoa.topo.json`, `data/site_lsoa.json`, `data/site.json` | Page data: simplified LSOA polygons (mapshaper, 15% of vertices), per-LSOA shares, cities, councils and places. |
| `data/lsoa_age.csv`, `data/msoa_age.csv`, `data/la_age.csv` | VOA counts tidied: homes by build period (single years from 2009), unknown, Council Tax band and property type, for LSOAs, MSOAs and local authorities. |
| `data/lsoa_measures.csv` | Per LSOA: shares by period and era, median period, mean build year, unknown share, nearest city and distance. |
| `data/la_rank.csv` | Local authorities: shares by era, mean year, median period. |
| `data/nation_band_period.csv` | Council Tax band by build period for England and Wales, England and Wales separately. |
| `data/cities.csv` | The 34 cities with Wikidata and Natural Earth centres. |
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

Hotham, T. (2026) How old is your neighbourhood? The age of the housing stock in every small area of England and Wales, and the tree rings of its cities. Zenodo. https://doi.org/10.5281/zenodo.24113860

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.

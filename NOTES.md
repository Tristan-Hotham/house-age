# house-age: working notes

Brief: /home/claude/work/new14/BRIEFS.md section J (+ shared rules: new12, new11, new10, new9, new8 tops, house brief
/home/claude/newdata/BRIEF.md, GIF brief /home/claude/gifs/BRIEF.md). Format refs: day-from-london, sea-view, janus-places.
Scratch: /home/claude/scratch/house-age (LSOA boundaries gpkg, intermediates; delete by exact path at the end).

## Data in hand (checked before the plan; no outcome computed yet)
- VOA, Council Tax: stock of properties 2025 (first released 25 Sep 2025, updated 22 May 2026; data at 31 March 2025),
  Official Statistics, OGL v3. CTSOP4.1 (band x build period) and CTSOP3.1 (band x property type x bedrooms), rows for
  E&W, nations, regions, counties, LAs (LAUA), MSOA 2021 and LSOA 2021 (35,672 LSOAs = 33,755 England + 1,917 Wales, so
  2021 codes). LSOA/MSOA rows assign properties by postcode (NSPL, Feb 2025; VOA "Method 2").
- Counts rounded to the nearest 10; counts under five shown as "-" in the CSV ("[c]" in the background note), so a "-"
  cell is 1 to 4 properties; "0" is a true zero.
- Build periods: pre-1900, 1900-1918, 1919-1929, 1930-1939, 1945-1954, 1955-1964, 1965-1972, 1973-1982, 1983-1992,
  1993-1999, 2000-2008, then single years 2009 to 2025 (2025 = 1 Jan to 31 Mar only), unknown. VOA: no age code for
  1940 to 1944 "because no properties are recorded as built in this time period". I combine 2009-2025 as "2009 onwards"
  for the main periods and keep single years for the new-build analysis.
- Boundaries: ONS LSOA 2021 generalised clipped (BGC), OGL, via the GitHub copy drkane/geo-lookups
  (commit e20a072d5fc0918437abaa3622be63f40b71d9dd, boundaries/lsoa/E12*.geojson and W06*.geojson). All 35,672 codes.
  ONS MSOA 2021 BSC and LAD 2023 from /home/claude/newdata/raw/geo.
- City centres: Natural Earth populated places with pop_max >= 100,000 in England and Wales (34 places: the list of
  cities); centre coordinates taken from the Wikidata item of the same city (uk_settlements.tsv; more precise), with
  Natural Earth's own coordinates as a sensitivity check.

## Analysis plan (written 2026-11-10T13:25Z, before any LSOA-level or distance outcome was computed)

Question. How old are the homes of England and Wales, area by area, and is there a regular spatial order to housing age
inside cities: do homes get newer with distance from the centre (the vintage or "tree ring" pattern of urban growth
models), and has the newest housing reversed that pattern by being built closer in? Descriptive and correlational; the
stock is what survives in 2025, so age patterns mix building, demolition and replacement. No causal claims.

Unit: LSOA 2021 (35,672). Homes = Council Tax domestic properties (all bands, all types, incl. annexes and caravans).
Main counts: "-" = 0 (sensitivity: "-" = 2.5). Unknown build period excluded from shares of known homes; its share is
reported separately.

### Measures per LSOA
- Share of known homes in each of 12 periods (2009 onwards combined), and in groups: before 1919, interwar (1919-1939),
  post-war (1945-1972), 1973-1999, 2000-2008, 2009 onwards.
- Median build period: the period containing the 50th percentile of known homes in the chronological order.
- Mean build year (for regressions): period midpoints (pre-1900 = 1875, 1900-1918 = 1909, 1919-1929 = 1924, 1930-1939 =
  1934.5, 1945-1954 = 1949.5, ..., 2000-2008 = 2004, single years as given, 2025 = 2025). Sensitivity: pre-1900 = 1850
  and 1890.

### Estimands (reported whatever they show)
- D1 national and nation distribution by period; the unknown share (national, by LA; LSOAs above 10%).
- D2 LSOA distribution of median period; share of LSOAs whose median home is pre-1919, interwar, post-war, etc.
- D3 oldest and newest local authorities (share pre-1919, share 2009 onwards, median period), all LAs listed in data.
- D4 new-build frontier: LSOAs with at least half of known homes built 2009 onwards; homes built each year 2009 to 2024.
- D5 band by period (national cross-tab, England and Wales separately because bands use 1991 and 2003 values) and type
  by LSOA age (correlation of pre-1919 share with terraced share; post-war share with flats; 2009+ with flats/detached).

### Hypotheses about cities
Cities: the 34 E&W places above. Each LSOA is assigned to its nearest centre (LSOA population-weighted centroid is not
available, so the polygon's representative point, a point guaranteed inside the polygon); it is in a city's catchment
if within 20 km of that centre. Distance in km on the British National Grid.

- H1 (vintage gradient). Within cities, homes get newer with distance from the centre over 0 to 20 km.
  Model M1: LSOA mean build year = city fixed effects + distance (km, linear), weighted by known homes, SE clustered by
  local authority (LAD). Reported also with 1 km distance bins (0-1, ..., 19-20) to show the shape. Prediction: positive
  slope. Counts against: slope <= 0 or 95% CI including 0.
- H2 (rings in order). The homes of each successive period stand farther out, from before 1900 to 1965-1972.
  For each city c and period p (pre-1900 ... 1965-1972; 7 periods), D(c,p) = mean distance from the centre of the homes
  of period p within the catchment (LSOA representative points weighted by counts). Model M2: log D(c,p) = city FE +
  period index (0..6, linear), OLS, SE clustered by city. Prediction: positive coefficient; also the share of cities
  whose Spearman correlation between period order and D is positive. Counts against: coefficient <= 0 or CI includes 0.
- H3 (reversal at the edge). Homes built 2009 onwards stand closer to the centre than homes built 1983-1999 (the period
  of out-of-town estates before brownfield-first policy).
  Model M3: log D(c, 2009+) - log D(c, 1983-1999), mean across cities with a t-interval (cities as units), and the share
  of cities where it is negative. Prediction: negative. Counts against: CI includes 0 or positive. Also reported for
  every later period against 1983-1992 as a profile (descriptive).
- H4 (interwar belt). The interwar share peaks at an intermediate distance: for each city, the 1 km band with the
  highest interwar share lies farther out than the band with the highest pre-1919 share and nearer than the band with
  the highest 1955-1972 share. Reported as the share of cities meeting the order (descriptive; no test).

### Robustness and falsification (pre-specified)
- R1 "-" = 2.5 instead of 0.
- R2 pre-1900 midpoint 1850 and 1890 (M1).
- R3 catchment 10 km and 30 km.
- R4 centre coordinates from Natural Earth instead of Wikidata.
- R5 leave one region out (England's 9 regions and Wales), and London dropped.
- R6 placebo: each city centre moved 10 km in a random direction (200 draws, seed 1); recompute M1 slope and M2
  coefficient. If the real centres do not give clearly steeper gradients than the placebo centres (real slope above the
  95th percentile of placebo slopes), the "centre" interpretation fails.
- R7 restrict to LSOAs with unknown share below 2%.
- R8 SE clustered by city instead of LAD (M1); MSOA-level replication of M1 and M2.
- R9 M1 with distance bins and a quadratic, to check that a linear slope is not hiding a reversal.
Headline: report the main specification even if it disappoints; anything added later is labelled exploratory.

### What the data cannot show
Survivors only (slum clearance, war damage and redevelopment remove old homes; conversions split them); build period
is VOA's age code (an assessment, coarse before 1900); properties not homes (annexes, caravans counted); 2025 has one
quarter; Wales bands differ; LSOA boundaries are generalised; representative point not population centroid.

## Log
- 13:20 boundaries from drkane/geo-lookups (E12 region files + W06 Welsh LAs), merged to scratch/lsoa21_bgc.gpkg,
  35,672 unique LSOA21CD (33,755 E, 1,917 W).
- 13:27 01_prepare.py: 35,672 LSOAs, 7,264 MSOAs, 318 LAs; Barnsley and Sheffield 2024 recodes (E08000038/39) mapped to
  the VOA codes E08000016/19. LSOA sums match LA rows within 0.21%.
- 13:28 02_cities.py: 34 cities; Bradford has no Wikidata item in the extract, so its Natural Earth point is used.
- 13:30 03_analysis.py (main specification as planned):
  M1 0.605 years/km [0.362, 0.848] BUT fails the planned placebo rule (placebo p95 0.635; 8.5% of draws >= real).
  M2 0.0422 [0.0307, 0.0538] (4.3% per period), 33/34 cities positive rho (London -0.11); placebo max 0.014: passes.
  M3 -0.095 [-0.139, -0.050] (9% closer), 26/34 cities negative. H4 order in 32/34 (fails London, Exeter).
  All R1 to R9 keep M2 > 0 and M3 < 0 with CIs excluding zero. MSOA replication: M3 not computed (M1, M2 only).
- Implementation detail decided while coding (not in the plan text): H4 uses only 1 km bands with >= 1,000 homes of
  known age; profile figure over all 12 periods is descriptive. Exploratory (labelled in paper): within-LA regression of
  mean Council Tax band on mean build year (England).
- Page: MapLibre + topojson-client; LSOA TopoJSON simplified to 15% with mapshaper (quantisation 100,000 after review: 6.5 MB, 1.9 MB gzip).

## References: verification status
Verified online in this build (bibliographic details from publisher/RePEc/IDEAS pages or the PDF):
Brueckner and Rosenthal 2009 (abstract read; DOI seen); Rosenthal 2008 (abstract summary read); Glaeser and Gyourko
2005 (PDF title page read); Rosenthal 2014 (abstract sentence; DOI seen); Vigdor 2010 (abstract sentence); Arnott et al.
1999 (abstract sentence); Rodriguez-Bachiller 1986 (DOI seen; no abstract); Ioannides and Rossi-Hansberg 2008 (entry read);
Harrison and Kain 1974, Brueckner 1980, Wheaton 1982, Braid 2001 (bibliographic details only, no abstract read);
VOA 2025 background information and statistical commentary (read).
Bibliographic details only, from the IDEAS list of works citing Rosenthal 2008 (titles, venues, volumes, pages; no
abstract read, cited only for what the title states): Heblich, Trew and Zylberberg 2021; Hanlon and Heblich 2022;
Rosenthal and Ross 2015; Rolheiser 2021; Xu 2023; Waights 2019; Hilber, Rouwendal and Vermeulen 2021; Siodla 2015;
van Duijn and Rouwendal 2021; Malone and Redfearn 2018; Munneke and Womack 2015; Dube et al. 2018 (first author only).
The shared WebSearch budget ran out partway, so the UK housing-history literature (interwar suburbs, post-war
council housing, slum clearance, brownfield policy, English Housing Survey, Historic England) is NOT cited; candidates
for the reviewer: Whitehand 1967 (fringe belts, Trans IBG 41); Yelling 2000 (slum clearance, Urban History 27(2));
Bromley, Tallon and Thomas 2005 (Urban Studies 42(13)); Hilber and Vermeulen 2016 (Economic Journal 126); Jackson 1973
Semi-Detached London; English Housing Survey stock reports. Journal word limits in cover_note.md are also unchecked.

## Independent review (2026-11-10)
Recomputed national shares, Wales/England pre-1919, oldest/newest LAs, M1, M2, M3 and the 1 km new-build share from the raw VOA CSV and
the released LSOA tables: all match results.json. Added a verified paragraph on UK housing history (Jackson 1973; Boughton 2018;
Yelling 2000; Wong and Schulze Baing 2010; Bromley, Tallon and Thomas 2005; Whitehand 1967; English Housing Survey 2024 to 2025;
Historic England 2019), checked every other reference against IDEAS/RePEc or publisher pages and tightened descriptions to what
the abstracts say. Journal limits and fees checked (cover_note.md). Placebo share now printed as 8.5% (was rounded to 8%).

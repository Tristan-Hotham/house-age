**Title:** [OC] How old is your neighbourhood? Every one of the 35,672 small areas of England and Wales by the age of its homes: 21% of homes predate 1919, and within 1 km of city centres 32% were built since 2009

**Body:**

Every home on the Council Tax list has a build period, and the Valuation Office Agency publishes the counts for every small area (about 760 homes each on average). I mapped the build period of the median home in each one.

- England and Wales: 21% of homes built before 1919, 15% between the wars, 26% from 1945 to 1972, 12% since 2009. Wales is older (30% pre-1919) than England (20%).
- Oldest council: Kensington and Chelsea (66% pre-1919). Newest: Tower Hamlets (32% built since 2009).
- Cities grow in rings: in the 34 cities with 100,000+ people, each era's homes from before 1900 to 1965 to 1972 stand on average 4.3% farther from the centre than the last (33 of 34 cities). Moving the centres 10 km at random never reproduces this.
- Then it reverses: homes built since 2009 stand 9% closer to the centre than those of 1983 to 1999 (in 26 of 34 cities), and they are the largest group of homes within 1 km of the centres (32%).
- Caveats: these are the homes standing today, so demolished homes are missing; the build period is an administrative code (no code exists for 1940 to 1944); one centre per city is a simplification.

Interactive map (tap any area for its age profile, colour by any era): https://maps.tristanhotham.com/house-age/

**Source comment:**

Data: Valuation Office Agency, Council Tax: stock of properties 2025, tables CTSOP4.1 and CTSOP3.1 (Official Statistics, OGL); ONS LSOA 2021 boundaries (OGL); city list from Natural Earth, centres from Wikidata. Method: shares of homes by build period per LSOA; distance from each area to the nearest of 34 city centres; fixed-effects regressions with a placebo test, pre-specified in a written plan. Tools: Python (pandas, geopandas, statsmodels, matplotlib), MapLibre. Paper and code: https://github.com/Tristan-Hotham/house-age

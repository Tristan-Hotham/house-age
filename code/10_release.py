"""Step 10: blog post and meta (release/blog), Zenodo files and metadata (release/zenodo).
10.5281/zenodo.24113860, https://doi.org/10.5281/zenodo.24113860 and https://blog.tristanhotham.com/2026/10/31/house-age/ are left for the publisher to fill."""
import json as _json, shutil, zipfile
from PIL import Image
from common import *

R = jload(f"{DATA}/results.json")
NAME = "Hotham_House_Age"
KEEP = {"DOI", "DOI_URL", "BLOG_URL"}
post = open(os.path.join(CODE, "blog_template.html"), encoding="utf-8").read()


def fill(m):
    k, f = m.group(1), m.group(3)
    if k in KEEP: return m.group(0)
    return fmt(get(R, k), f)


post = re.sub(r"\{\{(?!IMG)([^}|]+)(\|(\w+))?\}\}", fill, post)
used = re.findall(r"\{\{IMG\|([^|]+)\|", post)
assert 5 <= len(used) <= 8, len(used)
assert all(re.search(r"^\{\{IMG\|" + re.escape(u_), post, re.M) for u_ in used) and "wp:image" not in post
for img in used:
    assert Image.open(f"{REL}/blog/{img}").size[0] == 1800, img
for fn in os.listdir(f"{REL}/blog"):
    if fn.startswith("b_") and fn not in used:
        os.remove(f"{REL}/blog/{fn}")
left = set(re.findall(r"\{\{([^|}]+)\}\}", post)) - {"IMG"}
assert left <= KEEP, left
vis = re.sub(r"<!--.*?-->", "", post, flags=re.S)
for bad in ("\u2014", "\u2013", "--", "DSIT", "DCMS", "civil serv", "pre-registered"):
    assert bad not in vis, bad
assert AI in post
open(f"{REL}/blog/post.html", "w", encoding="utf-8").write(post)
words = len(re.sub(r"<[^>]+>|\{\{IMG\|[^}]*\}\}", " ", vis).split())
N = R["nat"]["England and Wales"]
meta = {"title": "How old is your neighbourhood?",
        "slug": "house-age",
        "excerpt": f"Every home in England and Wales has a build period on the Council Tax list. I mapped all {R['meta']['n_lsoa']:,} small areas: {N['pre1919']:.0f}% of homes predate 1919 and {N['new']:.0f}% were built since 2009. Cities grow in rings of age, until recently, when the newest homes started coming back to the middle.",
        "seo_description": f"The age of the homes in every small area of England and Wales, mapped: {N['pre1919']:.0f}% predate 1919, and cities grow in rings.",
        "tags": ["maps", "data visualisation", "housing", "cities", "urban history", "Council Tax", "England", "Wales"],
        "header_alt": "Title card on light paper reading 'How old is your neighbourhood?' beside a map of England and Wales with every small area coloured from deep brown for Victorian homes to deep blue for homes built since 2009."}
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
_json.dump(meta, open(f"{REL}/blog/meta.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)

Z = f"{REL}/zenodo"; os.makedirs(Z, exist_ok=True)
for fn in os.listdir(Z):
    os.remove(os.path.join(Z, fn))
shutil.copy(f"{REL}/paper/{NAME}.pdf", f"{Z}/{NAME}.pdf")
zp = f"{Z}/{SLUG}_data_and_code.zip"
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for fn in sorted(os.listdir(CODE)):
        if fn.endswith(".pyc") or fn == "__pycache__":
            continue
        z.write(os.path.join(CODE, fn), f"{SLUG}/code/{fn}")
    for fn in sorted(os.listdir(DATA)):
        if fn.startswith("site") or fn.endswith(".topo.json"):
            continue   # page data, rebuilt by 06_site_data.py
        z.write(os.path.join(DATA, fn), f"{SLUG}/data/{fn}")
    for fn in ("README.md", "LICENSE", "NOTES.md"):
        z.write(os.path.join(ROOT, fn), f"{SLUG}/{fn}")
    z.write(os.path.join(REL, "paper", "cover_note.md"), f"{SLUG}/release/paper/cover_note.md")
    z.write(os.path.join(ROOT, "reddit", "collage.py"), f"{SLUG}/reddit/collage.py")
tex = open(f"{REL}/paper/{NAME}.tex", encoding="utf-8").read()
ab = re.search(r"\\begin\{center\}\\textbf\{Abstract\}\\end\{center\}\n(.*?)\n\n", tex, re.S).group(1)
ab = ab.replace("\\%", "%").replace("\\&", "&").replace("$-$", "-").replace("$", "").replace("``", "\"").replace("''", "\"")
ab = re.sub(r"\\[a-z]+\{([^}]*)\}", r"\1", ab)
zmeta = {"title": "How Old Is Your Neighbourhood? The Age of the Housing Stock in Every Small Area of England and Wales, and the Tree Rings of Its Cities",
         "upload_type": "publication", "publication_type": "workingpaper",
         "description": f"<p>{ab}</p><p>Interactive version: <a href=\"{PAGE}\">{PAGE}</a>. Data and code: <a href=\"{REPO}\">{REPO}</a>. Blog post: {{https://blog.tristanhotham.com/2026/10/31/house-age/}}.</p><p>Sources: Valuation Office Agency, Council Tax: stock of properties 2025, tables CTSOP3.1 and CTSOP4.1 (Official Statistics, Open Government Licence v3.0); ONS LSOA 2021 boundaries (Open Government Licence v3.0); Natural Earth (public domain); Wikidata (CC0). Text, figures and derived data CC BY 4.0; code MIT.</p>",
         "creators": [{"name": "Hotham, Tristan", "affiliation": "Independent researcher", "orcid": "0000-0003-4931-9349"}],
         "keywords": ["housing stock", "dwelling age", "urban growth", "vintage models", "recentralisation", "Council Tax", "LSOA", "England and Wales"],
         "license": "cc-by-4.0", "language": "eng",
         "related_identifiers": [{"identifier": REPO, "relation": "isSupplementedBy", "resource_type": "software"},
                                 {"identifier": PAGE, "relation": "isSupplementedBy", "resource_type": "other"}],
         "files": sorted(os.listdir(Z))}
sj = _json.dumps(zmeta, ensure_ascii=False) + _json.dumps(meta, ensure_ascii=False)
assert "\u2014" not in sj and "\u2013" not in sj and "--" not in sj
_json.dump(zmeta, open(f"{Z}/metadata.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("blog words", words, "figures", len(used), "; zenodo", sorted(os.listdir(Z)), os.path.getsize(zp) // 1024, "KB zip")

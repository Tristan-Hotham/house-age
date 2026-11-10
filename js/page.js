/* How old is your neighbourhood? Every LSOA of England and Wales coloured by the age of its homes (VOA Council Tax
 * stock of properties 2025). MapLibre on OpenFreeMap Positron; LSOA polygons from a simplified TopoJSON joined by
 * position to data/site_lsoa.json. Colour by the median build period, by the share of homes in a group of periods or a
 * single period, or by the share of unknown age. Dr Tristan Hotham, Independent researcher, 2026. MIT licence. */
(function () {
  'use strict';
  const qs = new URLSearchParams(location.search);
  const STYLE = 'https://tiles.openfreemap.org/styles/positron';
  const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const norm = s => String(s).normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  const small = matchMedia('(max-width:800px)').matches;
  const NODATA = '#D9D6CF';
  const SEQ = ['#FBF3DC', '#F6DFAE', '#EFC47E', '#E3A057', '#CF7A3C', '#B1552B', '#87361F', '#5A2014'];
  const SEQB = [0, 5, 10, 20, 30, 40, 50, 65, 101];
  const UNK = ['#F3F1EC', '#DCE4EA', '#B5C8D8', '#7E9FBD', '#4C77A0', '#24507E'];
  const UNKB = [0, 1, 2, 5, 10, 25, 101];
  let map = null, S = null, D = null, mode = 'median', timer = null, feats = null;
  document.getElementById('theme').addEventListener('click', () => { const r = document.documentElement, d = r.dataset.theme ? r.dataset.theme === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches; r.dataset.theme = d ? 'light' : 'dark'; });
  const ct = document.getElementById('cartouche'); const fold = f => ct.classList.toggle('folded', f);
  if (small) fold(true);
  document.getElementById('ctToggle').addEventListener('click', () => fold(!ct.classList.contains('folded')));
  document.getElementById('ctFold').addEventListener('click', () => fold(true));

  const modes = () => {
    const out = [['median', 'Median build period']];
    D.groups.filter(g => g.idx.length > 1).forEach(g => out.push(['g:' + g.k, 'Share built ' + g.label.replace(/^Before/, 'before').replace(/^Between/, 'between').replace(/^Post-war/, 'post-war')]));
    D.per.forEach((p, k) => out.push(['p:' + k, 'Share built ' + p.replace(/^Before/, 'before').replace(/onwards/, 'onwards')]));
    out.push(['unknown', 'Share of unknown age']);
    return out;
  };
  const steps = (prop, breaks, cols) => { const e = ['step', ['get', prop], cols[0]]; for (let k = 1; k < cols.length; k++) e.push(breaks[k], cols[k]); return e; };
  function colourExpr() {
    if (mode === 'median') return ['case', ['<', ['get', 'm'], 0], NODATA, ['match', ['get', 'm'], ...D.col.flatMap((c, k) => [k, c]), NODATA]];
    if (mode === 'unknown') return steps('u', UNKB, UNK);
    return ['case', ['==', ['get', 'k'], 0], NODATA, steps(mode.startsWith('g:') ? 'G' + mode.slice(2) : 'p' + mode.slice(2), SEQB, SEQ)];
  }
  function legend() {
    const kt = document.getElementById('keyTitle'), kb = document.getElementById('keyBody');
    if (mode === 'median') {
      kt.textContent = 'Median build period of homes';
      if (small) { kb.innerHTML = `<div class="bands">${D.col.map(c => `<span style="background:${c}"></span>`).join('')}</div><div class="bl"><span>pre-1900</span><span>1965</span><span>2009+</span></div>`; return; }
      kb.innerHTML = '<div class="pgrid">' + D.per.map((p, k) => `<span><i style="background:${D.col[k]}"></i>${esc(p)}</span>`).join('') + '</div>';
      return;
    }
    const isU = mode === 'unknown';
    const lab = isU ? 'Homes of unknown build period' : modes().find(m => m[0] === mode)[1].replace('Share built', 'Homes built');
    kt.textContent = lab;
    const cols = isU ? UNK : SEQ, br = isU ? UNKB : SEQB;
    kb.innerHTML = `<div class="bands">${cols.map(c => `<span style="background:${c}"></span>`).join('')}</div><div class="bl">${br.slice(0, -1).map(b => `<span>${b}%</span>`).join('')}</div>` +
      (!isU && mode.startsWith('p:') ? `<div class="row kx">England and Wales: ${D.nat[Object.keys(D.nat)[+mode.slice(2)]]}% of homes</div>` : '');
  }
  function setMode(m) {
    mode = m; document.getElementById('mode').value = m;
    if (map && map.getLayer('age')) map.setPaintProperty('age', 'fill-color', colourExpr());
    legend();
  }
  function popupHtml(i) {
    const p = S.p[i], n = S.n[i];
    let h = `<b class="t">${esc(S.names[i])}</b><div class="nt">${esc(S.lads[S.lad[i]])}${S.c[i] >= 0 ? ` · ${S.d[i].toFixed(1)} km from the centre of ${esc(D.cities[S.c[i]].n)}` : ''}</div>`;
    h += `<table><tr><td>Homes</td><td>about ${n.toLocaleString('en-GB')}</td></tr>`;
    if (S.m[i] >= 0) h += `<tr><td>Median home built</td><td><b>${esc(D.per[S.m[i]])}</b></td></tr><tr><td>Average build year</td><td>about ${S.y[i]}</td></tr>`;
    h += `<tr><td>Unknown age</td><td>${S.u[i]}%</td></tr></table>`;
    if (S.m[i] >= 0) {
      const mx = Math.max(...p, 1);
      h += '<div class="pl"><b>Share of homes by build period</b><table class="bars">' + D.short.map((s, k) => `<tr><td>${esc(s)}</td><td><span class="bar" style="width:${Math.max(p[k] / mx * 110, p[k] ? 2 : 0)}px;background:${D.col[k]}"></span> ${p[k]}%</td></tr>`).join('') + '</table></div>';
    }
    h += '<p class="nt">Valuation Office Agency, Council Tax stock of properties at 31 March 2025 (OGL). Counts rounded to 10; no age code exists for 1940 to 1944.</p>';
    return h;
  }
  function setup(topo) {
    feats = topojson.feature(topo, topo.objects.lsoa).features;
    feats.forEach((f, i) => {
      const pr = { i, m: S.m[i], u: S.u[i], k: S.m[i] >= 0 ? 1 : 0 };
      S.p[i].forEach((v, k) => pr['p' + k] = v);
      D.groups.forEach(g => pr['G' + g.k] = g.idx.reduce((a, k) => a + S.p[i][k], 0));
      f.properties = pr; f.id = i;
    });
    const firstSym = map.getStyle().layers.find(l => l.type === 'symbol');
    const before = firstSym ? firstSym.id : undefined;
    map.addSource('lsoa', { type: 'geojson', data: { type: 'FeatureCollection', features: feats }, attribution: 'Homes: Valuation Office Agency 2025 (OGL); areas: ONS LSOA 2021 (OGL)', tolerance: 0.25 });
    map.addLayer({ id: 'age', type: 'fill', source: 'lsoa', paint: { 'fill-color': colourExpr(), 'fill-opacity': ['interpolate', ['linear'], ['zoom'], 5, 0.9, 13, 0.72], 'fill-antialias': false } }, before);
    map.addLayer({ id: 'outline', type: 'line', source: 'lsoa', minzoom: 10, paint: { 'line-color': '#FFFFFF', 'line-width': ['interpolate', ['linear'], ['zoom'], 10, 0.3, 14, 1.2], 'line-opacity': 0.8 } }, before);
    map.addSource('hl', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } });
    map.addLayer({ id: 'hl', type: 'line', source: 'hl', paint: { 'line-color': '#1D2128', 'line-width': 2.4 } });
    const ring = (lo, la, km) => { const c = []; for (let a = 0; a <= 360; a += 4) { const r = a * Math.PI / 180; c.push([lo + km / (111.32 * Math.cos(la * Math.PI / 180)) * Math.cos(r), la + km / 110.57 * Math.sin(r)]); } return c; };
    map.addSource('rings', { type: 'geojson', data: { type: 'FeatureCollection', features: D.cities.map(c => ({ type: 'Feature', properties: {}, geometry: { type: 'LineString', coordinates: ring(c.lo, c.la, D.catch) } })) } });
    map.addLayer({ id: 'rings', type: 'line', source: 'rings', layout: { visibility: 'none' }, paint: { 'line-color': '#1D2128', 'line-width': 1.2, 'line-dasharray': [3, 2] } });
    map.addSource('cities', { type: 'geojson', data: { type: 'FeatureCollection', features: D.cities.map((c, i) => ({ type: 'Feature', properties: { i, n: c.n }, geometry: { type: 'Point', coordinates: [c.lo, c.la] } })) } });
    map.addLayer({ id: 'cities', type: 'circle', source: 'cities', paint: { 'circle-radius': ['interpolate', ['linear'], ['zoom'], 5, small ? 3.5 : 4, 9, 6, 13, 8], 'circle-color': '#1D2128', 'circle-stroke-color': '#fff', 'circle-stroke-width': 1.8 } });
    map.addLayer({ id: 'clbl', type: 'symbol', source: 'cities', minzoom: 6, layout: { 'text-field': ['get', 'n'], 'text-size': 12, 'text-font': ['Noto Sans Bold'], 'text-offset': [0, 0.9], 'text-anchor': 'top', 'text-optional': true }, paint: { 'text-color': '#1D2128', 'text-halo-color': '#fff', 'text-halo-width': 1.8 } });
    map.on('click', e => {
      const f = map.queryRenderedFeatures(e.point, { layers: ['age'] });
      if (!f.length) return;
      openArea(f[0].properties.i, e.lngLat);
    });
    map.on('mousemove', 'age', () => map.getCanvas().style.cursor = 'pointer');
    map.on('mouseleave', 'age', () => map.getCanvas().style.cursor = '');
    const lp = document.getElementById('lp'), btn = document.getElementById('lyrBtn');
    btn.addEventListener('click', e => { e.stopPropagation(); const o = lp.classList.toggle('open'); btn.setAttribute('aria-expanded', o); });
    document.addEventListener('click', e => { if (!lp.contains(e.target) && e.target !== btn) { lp.classList.remove('open'); btn.setAttribute('aria-expanded', false); } });
    const vis = (ids, v) => ids.forEach(id => map.setLayoutProperty(id, 'visibility', v ? 'visible' : 'none'));
    document.getElementById('lyA').addEventListener('change', e => vis(['age'], e.target.checked));
    document.getElementById('lyO').addEventListener('change', e => vis(['outline'], e.target.checked));
    document.getElementById('lyC').addEventListener('change', e => vis(['cities', 'clbl'], e.target.checked));
    document.getElementById('lyR').addEventListener('change', e => vis(['rings'], e.target.checked));
    const baseSym = map.getStyle().layers.filter(l => l.type === 'symbol' && l.id !== 'clbl').map(l => l.id);
    document.getElementById('lyB').addEventListener('change', e => vis(baseSym, e.target.checked));
    const sel = document.getElementById('mode');
    sel.innerHTML = modes().map(([v, l]) => `<option value="${v}">${esc(l)}</option>`).join('');
    sel.addEventListener('change', () => { stop(); setMode(sel.value); });
    const play = document.getElementById('play');
    function stop() { if (timer) { clearInterval(timer); timer = null; play.textContent = 'Play'; } }
    play.addEventListener('click', () => { if (timer) { stop(); return; } play.textContent = 'Pause'; let k = mode.startsWith('p:') ? +mode.slice(2) : -1;
      timer = setInterval(() => { k += 1; if (k > 11) { stop(); return; } setMode('p:' + k); }, 1500); });
    const m0 = qs.get('mode'); setMode(m0 && modes().some(m => m[0] === m0) ? m0 : 'median');
    document.getElementById('nojs').style.display = 'none';
    if (small) { const a = document.querySelector('.maplibregl-ctrl-attrib'); if (a) a.classList.remove('maplibregl-compact-show'); }
  }
  function bbox(i) { const g = feats[i].geometry; let x0 = 180, y0 = 90, x1 = -180, y1 = -90; const walk = c => { if (typeof c[0] === 'number') { x0 = Math.min(x0, c[0]); x1 = Math.max(x1, c[0]); y0 = Math.min(y0, c[1]); y1 = Math.max(y1, c[1]); } else c.forEach(walk); }; walk(g.coordinates); return [[x0, y0], [x1, y1]]; }
  function openArea(i, ll) {
    map.getSource('hl').setData({ type: 'FeatureCollection', features: [feats[i]] });
    if (!ll) { const b = bbox(i); ll = [(b[0][0] + b[1][0]) / 2, (b[0][1] + b[1][1]) / 2]; }
    new maplibregl.Popup({ maxWidth: '340px', anchor: small ? 'bottom' : undefined }).setLngLat(ll).setHTML(popupHtml(i)).addTo(map)
      .on('close', () => map.getSource('hl').setData({ type: 'FeatureCollection', features: [] }));
  }
  function go(it) {
    fold(true);
    if (it.k === 'area') { const b = bbox(it.i); map.fitBounds(b, { padding: 80, maxZoom: 14, duration: 1000 }); map.once('moveend', () => openArea(it.i)); return; }
    if (it.k === 'la') { map.fitBounds([[it.o.b[0], it.o.b[1]], [it.o.b[2], it.o.b[3]]], { padding: 30, duration: 1000 }); return; }
    map.flyTo({ center: [it.o.lo, it.o.la], zoom: it.k === 'city' ? 10.4 : 12.5, duration: 1100 });
    map.once('moveend', () => { const p = map.project([it.o.lo, it.o.la]); const f = map.queryRenderedFeatures(p, { layers: ['age'] }); if (f.length && it.k !== 'city') openArea(f[0].properties.i, [it.o.lo, it.o.la]); });
  }
  function setupSearch() {
    const q = document.getElementById('q'), sug = document.getElementById('sug'); let items = [], k = -1;
    const idx = [].concat(D.cities.map(o => ({ t: o.n, s: 'city', k: 'city', o })), D.las.map(o => ({ t: o.n, s: 'council', k: 'la', o })),
      D.places.map(o => ({ t: o.n, s: 'place', k: 'place', o })), S.names.map((n, i) => ({ t: n, s: S.codes[i], k: 'area', i })));
    idx.forEach(x => x.nn = norm(x.t));
    const show = () => { const v = norm(q.value.trim()); sug.innerHTML = ''; k = -1; if (v.length < 2) { sug.style.display = 'none'; return; }
      const a = [], b = [];
      for (const x of idx) { if (x.nn.startsWith(v)) a.push(x); else if (v.length > 2 && x.nn.includes(v)) b.push(x); if (a.length > 14) break; }
      items = a.concat(b).slice(0, 12);
      items.forEach((it, j) => { const li = document.createElement('li'); li.setAttribute('role', 'option'); li.innerHTML = `${esc(it.t)} <span>${esc(it.s)}</span>`; li.addEventListener('mousedown', e => { e.preventDefault(); pick(j); }); sug.appendChild(li); });
      sug.style.display = items.length ? 'block' : 'none'; };
    const pick = j => { const it = items[j]; if (!it) return; q.value = it.t; sug.style.display = 'none'; go(it); };
    q.addEventListener('input', show);
    q.addEventListener('keydown', e => { const lis = [...sug.children];
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') { e.preventDefault(); k = Math.max(0, Math.min(lis.length - 1, k + (e.key === 'ArrowDown' ? 1 : -1))); lis.forEach((l, i) => l.setAttribute('aria-selected', i === k)); }
      else if (e.key === 'Enter') { e.preventDefault(); if (!items.length) show(); pick(k < 0 ? 0 : k); } else if (e.key === 'Escape') sug.style.display = 'none'; });
    q.addEventListener('blur', () => setTimeout(() => sug.style.display = 'none', 150));
    const chips = document.getElementById('chips');
    ['London', 'Birmingham', 'Manchester', 'Leeds', 'Liverpool', 'Bristol', 'Newcastle upon Tyne', 'Cardiff', 'Sheffield', 'Nottingham'].forEach(n => {
      const o = D.cities.find(c => c.n === n); if (!o) return;
      const b = document.createElement('button'); b.className = 'chip'; b.textContent = n.replace(' upon Tyne', ''); b.addEventListener('click', () => go({ k: 'city', o })); chips.appendChild(b); });
    document.querySelectorAll('[data-go]').forEach(a => a.addEventListener('click', e => { e.preventDefault(); const [n, m] = a.dataset.go.split('|'); const o = D.cities.find(c => c.n === n);
      if (m) setMode(m); document.getElementById('mapWrap').scrollIntoView({ behavior: 'smooth' }); if (o) go({ k: 'city', o }); }));
  }
  Promise.all([fetch('data/site.json').then(r => r.json()), fetch('data/site_lsoa.json').then(r => r.json())]).then(([d, s]) => {
    D = d; S = s; legend();
    const at = (qs.get('at') || '').split(',').map(Number);
    const mo = at.length === 3 && at.every(isFinite) ? { center: [at[1], at[0]], zoom: at[2] } : { bounds: [[-5.8, 49.95], [1.8, 55.8]], fitBoundsOptions: { padding: small ? { top: 60, bottom: 90, left: 10, right: 10 } : { top: 40, bottom: 70, left: 360, right: 60 } } };
    const m0 = new maplibregl.Map(Object.assign({ container: 'map', style: STYLE, attributionControl: { compact: true }, maxZoom: 15, minZoom: 4.5 }, mo));
    m0.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'bottom-right');
    window.__map = m0; map = m0;
    setupSearch();
    return Promise.all([new Promise((res, rej) => { m0.once('load', res); m0.once('error', e => { if (!m0.loaded()) rej(e.error || e); }); }), fetch('data/lsoa.topo.json').then(r => r.json())]);
  }).then(([, topo]) => setup(topo)).catch(err => { document.getElementById('nojs').textContent = 'The map could not load: ' + err; console.error(err); });
})();

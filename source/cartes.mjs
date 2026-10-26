// Prépare les cartes de chaque continent (chemins SVG déjà projetés) à partir de Natural Earth 1:50m.
// Lancer depuis source/ : npm install puis node cartes.mjs (écrit cartes.json, lu par build.py)
import fs from "fs";
import * as d3 from "d3-geo";
import * as topo from "topojson-client";
import * as simp from "topojson-simplify";
const monde = JSON.parse(fs.readFileSync("node_modules/world-atlas/countries-50m.json"));
const wc = JSON.parse(fs.readFileSync("node_modules/world-countries/countries.json"));
const lignes = fs.readFileSync("pays.txt", "utf8").split("\n").filter(l => l && !l.startsWith("#")).map(l => l.split("|"));
const PAYS = lignes.map(([code, cont, ue, nom, cap, lat, lon]) => ({ code, cont, ue: ue === "1", nom, cap, lat: +lat, lon: +lon }));
const num2code = {}; for (const c of wc) if (c.ccn3) num2code[c.ccn3] = c.cca2;

let t = simp.presimplify(monde);
t = simp.simplify(t, simp.quantile(t, 0.35));
const feats = topo.feature(t, t.objects.countries).features;
// rattacher les morceaux sans code au pays que les enfants connaissent
const fusion = { "Somaliland": "SO", "N. Cyprus": "CY", "Kosovo": "XK", "Siachen Glacier": "IN" };
const parCode = {};
for (const f of feats) {
  const code = f.id ? num2code[f.id] : fusion[f.properties.name];
  const k = code || "_" + f.properties.name;
  (parCode[k] = parCode[k] || []).push(f);
}
// couleurs : deux pays voisins n'ont jamais la même (6 couleurs pastel)
const geoms = t.objects.countries.geometries, voisins = topo.neighbors(geoms), codeDe = i => geoms[i].id ? num2code[geoms[i].id] : fusion[geoms[i].properties.name];
const autour = {};
geoms.forEach((g, i) => { const c = codeDe(i); if (!c) return; autour[c] = autour[c] || new Set(); voisins[i].forEach(j => { const v = codeDe(j); if (v && v !== c) autour[c].add(v); }); });
const couleurs = {};
for (const c of Object.keys(autour).sort((a, b) => autour[b].size - autour[a].size)) {
  const prises = new Set([...autour[c]].map(v => couleurs[v]));
  couleurs[c] = [0, 1, 2, 3, 4, 5].find(n => !prises.has(n)) ?? 0;
}
const geomDe = l => ({ type: "Feature", geometry: { type: "MultiPolygon", coordinates: l.flatMap(f => f.geometry.type === "Polygon" ? [f.geometry.coordinates] : f.geometry.coordinates) } });

const CARTES = {
  EU:  { rot: [-15, -52], lon: [-25, 46], lat: [34, 71.5] },
  UE:  { rot: [-12, -50], lon: [-11, 35], lat: [34.5, 70.5], ue: true },
  AF:  { rot: [-17, -2],  lon: [-26, 58], lat: [-36, 38] },
  AS:  { rot: [-88, -28], lon: [26, 148], lat: [-11, 55] },
  AN:  { rot: [95, -42],  lon: [-168, -55], lat: [7, 72] },
  AS2: { rot: [60, 18],   lon: [-82, -34], lat: [-56, 13] },
  OC:  { rot: [-160, 18], lon: [110, 190], lat: [-48, 12] },
};
const W = 1000, PETIT = 90; // en dessous de cette surface (px²), le pays devient un rond
const r1 = n => Math.round(n * 10) / 10;
const sortie = {};
for (const [id, c] of Object.entries(CARTES)) {
  const cadre = [];
  for (let i = 0; i <= 20; i++) { const lo = c.lon[0] + (c.lon[1] - c.lon[0]) * i / 20, la = c.lat[0] + (c.lat[1] - c.lat[0]) * i / 20; cadre.push([lo, c.lat[0]], [lo, c.lat[1]], [c.lon[0], la], [c.lon[1], la]); }
  const p = d3.geoAzimuthalEqualArea().rotate(c.rot).fitWidth(W, { type: "MultiPoint", coordinates: cadre });
  const b = d3.geoPath(p).bounds({ type: "MultiPoint", coordinates: cadre });
  const H = Math.round(b[1][1] - b[0][1]);
  p.translate([p.translate()[0] - b[0][0], p.translate()[1] - b[0][1]]).clipExtent([[-W * .3, -H * .15], [W * 1.3, H * 1.15]]); // un peu de marge : la carte remplit aussi les écrans plus larges
  const chemin = d3.geoPath(p).digits(1);
  const cheminFond = d3.geoPath(p).digits(0); // le fond n'a pas besoin d'autant de précision
  const joue = PAYS.filter(x => c.ue ? x.ue : x.cont === id);
  const codes = new Set(joue.map(x => x.code));
  const fond = [], pays = {}, petits = {}, noms = {}, caps = {};
  for (const [k, l] of Object.entries(parCode)) {
    const g = geomDe(l);
    if (!codes.has(k)) { const d = cheminFond(g); if (d) fond.push(d); continue; }
    const d = chemin(g);
    if (!d) continue;
    pays[k] = d;
    // le plus grand morceau sert à placer le nom
    const morceaux = g.geometry.coordinates.map(co => ({ type: "Polygon", coordinates: co }));
    const grand = morceaux.reduce((a, m) => d3.geoPath(p).area(m) > d3.geoPath(p).area(a) ? m : a);
    const aire = d3.geoPath(p).area(g);
    const [x, y] = d3.geoPath(p).centroid(grand);
    noms[k] = [r1(x), r1(y)];
    if (aire < PETIT) petits[k] = 1;
  }
  for (const x of joue) {
    const pt = p([x.lon, x.lat]);
    caps[x.code] = [r1(pt[0]), r1(pt[1])];
    if (!pays[x.code]) { petits[x.code] = 1; noms[x.code] = caps[x.code]; }
    else if (petits[x.code] && x.code !== "XK") noms[x.code] = noms[x.code];
  }
  sortie[id] = { w: W, h: H, fond: fond.join(""), pays, petits: Object.keys(petits), noms, caps };
  const manque = joue.filter(x => !pays[x.code]).map(x => x.code);
  console.log(id, "h", H, "pays", Object.keys(pays).length + "/" + joue.length, "petits", Object.keys(petits).join(","), "sans forme", manque.join(","), "taille", JSON.stringify(sortie[id]).length);
}
sortie.couleurs = couleurs;
fs.writeFileSync("cartes.json", JSON.stringify(sortie));

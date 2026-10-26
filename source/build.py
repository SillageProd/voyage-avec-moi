# Construit le site à mettre en ligne à partir de app.html. Deux éditions sortent du même code :
#   racine du dépôt  « Voyage avec moi » (français)
#   nl/              « Reis met mij » (néerlandais, noms de pays-nl.txt)
# Les données (pays.txt, pays-nl.txt et cartes.json) sont glissées dans la page, pour que tout marche hors ligne.
# Si pays.txt change : npm install puis node cartes.mjs, avant de lancer python3 build.py.
import json, pathlib, re, time
from PIL import Image, ImageDraw, ImageFont
ici = pathlib.Path(__file__).parent
site = ici.parent
source = (ici / "app.html").read_text()
numero = re.search(r'const VERSION = "([0-9.]+)"', source).group(1)
version = time.strftime("%Y%m%d%H%M%S")

def lignes(nom):
    return [l.split("|") for l in (ici / nom).read_text().splitlines() if l.strip() and not l.startswith("#")]
nl = {code: rest for code, *rest in lignes("pays-nl.txt")}
pays = []
for code, cont, ue, nom, cap, lat, lon in lignes("pays.txt"):
    pays.append([code, cont, int(ue), nom, cap] + nl.pop(code))
assert not nl, nl
cartes = json.loads((ici / "cartes.json").read_text())
assert sum(p[2] for p in pays) == 27
donnees = "const PAYS_BRUTS = " + json.dumps(pays, ensure_ascii=False) + ";\nconst CARTES = " + json.dumps(cartes, separators=(",", ":")) + ";"
assert source.count("/*DONNEES*/") == 1
source = source.replace("/*DONNEES*/", donnees)

def remplacer(texte, avant, apres):
    assert texte.count(avant) == 1, avant
    return texte.replace(avant, apres)

def construire(dossier, src, nom, lang, cache, exclure=""):
    dossier.mkdir(exist_ok=True)
    tete, corps = src.split('<div id="app"></div>', 1)
    tete = tete.replace('<meta name="claude:viewport-fit-sides" content="cover">\n', "")
    html = f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#dcefff">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<link rel="manifest" href="manifest.webmanifest">
<link rel="apple-touch-icon" href="icone-180.png">
<link rel="icon" href="icone-192.png">
<style>:root{{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}}html{{box-sizing:border-box}}body{{margin:0}}img{{max-width:100%}}[hidden]{{display:none!important}}</style>
{tete}</head>
<body>
<div id="app"></div>{corps}
<script>if ("serviceWorker" in navigator) navigator.serviceWorker.register("sw.js").catch(() => {{}});</script>
</body>
</html>
"""
    (dossier / "index.html").write_text(html)
    (dossier / "version.json").write_text('{ "version": "' + numero + '" }\n')
    (dossier / "manifest.webmanifest").write_text(f"""{{
  "name": "{nom}",
  "short_name": "{nom}",
  "lang": "{lang}",
  "start_url": "./",
  "scope": "./",
  "display": "standalone",
  "background_color": "#dcefff",
  "theme_color": "#dcefff",
  "icons": [
    {{ "src": "icone-192.png", "sizes": "192x192", "type": "image/png" }},
    {{ "src": "icone-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable" }}
  ]
}}
""")
    (dossier / "sw.js").write_text(f"""// Fonctionnement hors ligne : l'app (cartes comprises) est gardée en cache.
const CACHE = "{cache}-{version}";
const BASE = ["./", "index.html", "manifest.webmanifest", "icone-180.png", "icone-192.png", "icone-512.png"];
self.addEventListener("install", e => {{ e.waitUntil(caches.open(CACHE).then(c => c.addAll(BASE)).then(() => self.skipWaiting())); }});
self.addEventListener("activate", e => {{ e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k.startsWith("{cache}-") && k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim())); }});
self.addEventListener("fetch", e => {{
  const url = new URL(e.request.url);
  const garder = url.origin === self.location.origin || ["fonts.googleapis.com", "fonts.gstatic.com"].includes(url.hostname);
  if (e.request.method !== "GET" || !garder || url.pathname.endsWith("version.json")) return;{exclure}
  // la page : d'abord le réseau (pour les mises à jour), sinon le cache
  if (e.request.mode === "navigate") {{
    e.respondWith(fetch(e.request).then(r => {{ const c = r.clone(); caches.open(CACHE).then(k => k.put("index.html", c)); return r; }}).catch(() => caches.match("index.html")));
    return;
  }}
  e.respondWith(caches.match(e.request).then(m => m || fetch(e.request).then(r => {{
    if (r.ok || r.type === "opaque") {{ const c = r.clone(); caches.open(CACHE).then(k => k.put(e.request, c)); }}
    return r;
  }})));
}});
""")
    for t in (180, 192, 512): icone(t).save(dossier / f"icone-{t}.png")
    return len(html) // 1024

# icônes : un cadre blanc à bord violet sur fond bleu ciel, avec un globe
def icone(taille):
    s = 4; T = taille * s
    im = Image.new("RGB", (T, T), "#dcefff"); d = ImageDraw.Draw(im)
    m = int(T * .14); b = int(T * .05)
    d.rounded_rectangle([m, m, T-m, T-m], radius=int(T*.12), fill="#7176d6")
    d.rounded_rectangle([m+b, m+b, T-m-b, T-m-b], radius=int(T*.09), fill="#ffffff")
    emoji = Image.new("RGBA", (160, 160)); f = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf", 109)
    ImageDraw.Draw(emoji).text((80, 80), "🌍", font=f, embedded_color=True, anchor="mm")
    emoji = emoji.crop(emoji.getbbox()); c = int(T * .5)
    emoji = emoji.resize((c, c), Image.LANCZOS)
    im.paste(emoji, ((T - c) // 2, (T - c) // 2), emoji)
    return im.resize((taille, taille), Image.LANCZOS)

# édition française : le service worker laisse l'édition NL à son propre service worker
ko = construire(site, source, "Voyage avec moi", "fr", "voyage-avec-moi",
                exclure='\n  if (url.origin === self.location.origin && url.pathname.includes("/nl/")) return;')

# édition néerlandaise
nl = remplacer(source, 'const EDITION = "fr";', 'const EDITION = "nl";')
nl = remplacer(nl, "<title>Voyage avec moi</title>", "<title>Reis met mij</title>")
nl = remplacer(nl, 'content="Voyage avec moi"', 'content="Reis met mij"')
construire(site / "nl", nl, "Reis met mij", "nl-BE", "reis-met-mij")
print("ok", version, "v" + numero, ko, "Ko")

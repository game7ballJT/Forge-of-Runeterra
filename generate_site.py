#!/usr/bin/env python3
"""
Forge of Runeterra — Static Site Generator
Generates all crawlable, AI-indexable pages for GitHub Pages deployment.

Run:  python3 generate_site.py
Output: ./site/  (upload this folder's contents to your GitHub repo root)
"""

import re, json, os, textwrap
from pathlib import Path

# ──────────────────────────────────────────────
# LOAD DATA
# ──────────────────────────────────────────────
with open('all_data.json') as f:
    D = json.load(f)

ENTRIES          = D['entries']          # [[name, id, title, tags_str], ...]
ROLE_MAP         = D['role_map']         # {name: [roles]}
TIER_MAP         = D['tier_map']         # {name: 'S'/'A'/...}
BUILD_ITEMS      = D['build_items']      # {type: [items]}
KEYSTONES        = D['keystones']        # {type: {name,path,slots,...}}
COUNTERS_BY_TAG  = D['counters_by_tag']  # {tag: [champ names]}
LP_DATA          = D['lp_data']          # {name: {secondary,overview}}
GUIDES_DATA      = D['guides_data']      # {name: playstyle string}
POPULAR_BUILDS   = D['popular_builds']   # [{champ,type,items,note}]

PATCH      = '26.13'
PATCH_DATE = 'June 24, 2026'
BASE_URL   = 'https://forgeofruneterra.gg'
DD_CDN     = 'https://ddragon.leagueoflegends.com/cdn/15.12.1/img'

# Build champion lookup dict
CHAMPS = {}
for name, cid, title, tags_str in ENTRIES:
    tags = re.findall(r'"([^"]+)"', tags_str)
    roles = ROLE_MAP.get(name, ['mid'])
    primary_role = roles[0]
    tier = TIER_MAP.get(name, 'B')
    build_type = ('ADC' if 'Marksman' in tags else
                  'Mage' if 'Mage' in tags else
                  'Fighter' if 'Fighter' in tags else
                  'Assassin' if 'Assassin' in tags else
                  'Tank' if 'Tank' in tags else
                  'Support' if 'Support' in tags else 'Fighter')
    items = BUILD_ITEMS.get(build_type, BUILD_ITEMS['Fighter'])
    runes = KEYSTONES.get(build_type, KEYSTONES['Fighter'])
    counters = COUNTERS_BY_TAG.get(tags[0] if tags else 'Fighter', [])
    lp = LP_DATA.get(name, {'secondary': [], 'overview': ''})
    playstyle = GUIDES_DATA.get(name, lp.get('overview', ''))

    CHAMPS[name] = {
        'name': name, 'id': cid, 'title': title, 'tags': tags,
        'primary_role': primary_role,
        'secondary_roles': lp.get('secondary', []),
        'tier': tier,
        'build_type': build_type,
        'items': items,
        'runes': runes,
        'counters': counters,
        'overview': lp.get('overview', ''),
        'playstyle': playstyle,
        'slug': cid.lower(),
    }

ROLE_DISPLAY = {'top':'Top Lane','jungle':'Jungle','mid':'Mid Lane','adc':'ADC (Bot Lane)','support':'Support'}

def role_label(r):
    return ROLE_DISPLAY.get(r, r.title())

def img(cid):
    return f"{DD_CDN}/champion/{cid}.png"

def item_img(item_name):
    # Static item IDs for common items
    ITEM_IDS = {
        "Kraken Slayer": "6672", "Galeforce": "6671", "Infinity Edge": "3031",
        "Phantom Dancer": "3046", "Mortal Reminder": "3033",
        "Lord Dominik's Regards": "3036",
        "Luden's Tempest": "6655", "Shadowflame": "4645",
        "Zhonya's Hourglass": "3157", "Void Staff": "3135",
        "Rabadon's Deathcap": "3089", "Morellonomicon": "3165",
        "Trinity Force": "3078", "Black Cleaver": "3071",
        "Sterak's Gage": "3053", "Death's Dance": "6333",
        "Ravenous Hydra": "3074", "Sundered Sky": "6694",
        "Duskblade of Draktharr": "6691", "Edge of Night": "6692",
        "Serpent's Fang": "6694", "Axiom Arc": "6695",
        "Sunfire Aegis": "3068", "Warmog's Armor": "3083",
        "Thornmail": "3075", "Gargoyle Stoneplate": "3193",
        "Locket of the Iron Solari": "3190", "Redemption": "3107",
        "Shurelya's Battlesong": "2065", "Moonstone Renewer": "6617",
    }
    iid = ITEM_IDS.get(item_name, '3364')
    return f"{DD_CDN}/item/{iid}.png"

# ──────────────────────────────────────────────
# SHARED STYLES
# ──────────────────────────────────────────────
CSS = """
:root{
  --gold:#c8aa6e;--gold-dark:#a08040;--teal:#0bc4b4;
  --bg:#0a0e1a;--bg-card:#111827;--bg-panel:#0d1424;
  --border:rgba(255,255,255,.08);--text:#e2e8f0;--muted:#8899aa;
  --font:'Inter',system-ui,sans-serif;--display:'Cinzel','Trajan Pro',serif;
  --red:#ff4e50;--green:#22cc44;
}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--text);font-family:var(--font);font-size:16px;line-height:1.6}
a{color:var(--teal);text-decoration:none}a:hover{text-decoration:underline}
h1,h2,h3,h4{font-family:var(--display);color:var(--gold);line-height:1.3}
h1{font-size:clamp(1.8rem,4vw,2.8rem);margin-bottom:.5rem}
h2{font-size:clamp(1.2rem,2.5vw,1.7rem);margin:2rem 0 .75rem;padding-bottom:.4rem;border-bottom:1px solid var(--border)}
h3{font-size:1.1rem;margin:1.5rem 0 .5rem;color:var(--gold-dark)}
p{margin-bottom:1rem;color:#ccd6e8}
.container{max-width:1100px;margin:0 auto;padding:0 1.5rem}
.site-header{background:rgba(10,14,26,.95);border-bottom:1px solid var(--border);padding:.9rem 0;position:sticky;top:0;z-index:100;backdrop-filter:blur(10px)}
.site-header .inner{max-width:1100px;margin:0 auto;padding:0 1.5rem;display:flex;align-items:center;gap:1.5rem;flex-wrap:wrap}
.site-logo{font-family:var(--display);font-size:1.2rem;color:var(--gold);font-weight:700;letter-spacing:.05em}
.site-logo span{color:var(--teal);font-size:.65rem;display:block;letter-spacing:.15em;text-transform:uppercase}
.header-nav{display:flex;gap:1.2rem;font-size:.85rem}
.header-nav a{color:var(--muted)}
.header-nav a:hover{color:var(--gold);text-decoration:none}
.launch-btn{margin-left:auto;background:var(--teal);color:#000;padding:.45rem 1.1rem;border-radius:4px;font-weight:700;font-size:.82rem;text-decoration:none !important;letter-spacing:.05em}
.launch-btn:hover{background:#0ae0ce;color:#000}
.hero{padding:3rem 0 2rem;border-bottom:1px solid var(--border)}
.champ-hero{display:flex;align-items:flex-start;gap:1.5rem;flex-wrap:wrap}
.champ-splash{width:96px;height:96px;border-radius:8px;border:2px solid var(--border);object-fit:cover;flex-shrink:0}
.champ-meta{flex:1;min-width:0}
.champ-subtitle{color:var(--muted);font-size:.9rem;margin-bottom:.5rem}
.tags{display:flex;flex-wrap:wrap;gap:.4rem;margin:.5rem 0}
.tag{background:rgba(200,170,110,.12);color:var(--gold);border:1px solid rgba(200,170,110,.25);border-radius:4px;padding:2px 9px;font-size:.72rem;font-weight:600;letter-spacing:.06em;text-transform:uppercase}
.tag.role{background:rgba(11,196,180,.1);color:var(--teal);border-color:rgba(11,196,180,.25)}
.tag.tier-S{background:rgba(255,215,0,.15);color:#ffd700;border-color:rgba(255,215,0,.3)}
.tag.tier-A{background:rgba(192,57,43,.15);color:#e74c3c;border-color:rgba(192,57,43,.3)}
.tag.tier-B{background:rgba(52,152,219,.12);color:#3498db;border-color:rgba(52,152,219,.3)}
.tag.tier-C{background:rgba(149,165,166,.1);color:#95a5a6;border-color:rgba(149,165,166,.25)}
.tag.tier-D{background:rgba(100,100,100,.1);color:#7f8c8d;border-color:rgba(100,100,100,.2)}
.panel{background:var(--bg-card);border:1px solid var(--border);border-radius:8px;margin-bottom:1.5rem;overflow:hidden}
.panel-header{padding:.7rem 1.1rem;background:rgba(200,170,110,.06);border-bottom:1px solid var(--border);font-family:var(--display);font-size:.78rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--gold);display:flex;align-items:center;gap:.5rem}
.panel-body{padding:1.1rem}
.answer-first strong{color:#fff;font-size:1.05em;display:block;margin-bottom:.5rem}
.items-grid{display:flex;flex-wrap:wrap;gap:.6rem}
.item-chip{display:flex;align-items:center;gap:.45rem;background:rgba(255,255,255,.05);border:1px solid var(--border);border-radius:5px;padding:.3rem .55rem;font-size:.78rem;color:var(--text)}
.item-chip img{width:26px;height:26px;border-radius:3px;object-fit:cover}
.rune-block{display:flex;flex-direction:column;gap:.5rem}
.rune-keystone{background:rgba(200,170,110,.08);border:1px solid rgba(200,170,110,.2);border-radius:6px;padding:.7rem 1rem;font-weight:700;color:var(--gold)}
.rune-tree-label{font-size:.65rem;text-transform:uppercase;letter-spacing:.1em;color:var(--muted);margin:.6rem 0 .3rem}
.rune-chips{display:flex;flex-wrap:wrap;gap:.35rem}
.rune-chip{font-size:.77rem;padding:3px 9px;background:rgba(255,255,255,.05);border:1px solid var(--border);border-radius:3px;color:var(--text)}
.shard-chip{font-size:.72rem;padding:2px 7px;background:rgba(200,170,110,.07);border:1px solid rgba(200,170,110,.18);border-radius:3px;color:var(--gold-dark)}
.counter-grid,.synergy-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:.6rem}
.counter-card,.synergy-card{display:flex;align-items:center;gap:.5rem;background:rgba(255,255,255,.04);border:1px solid var(--border);border-radius:5px;padding:.4rem .6rem;font-size:.82rem}
.counter-card img,.synergy-card img{width:32px;height:32px;border-radius:4px;object-fit:cover}
.counter-card a,.synergy-card a{color:var(--text);text-decoration:none}
.counter-card a:hover,.synergy-card a:hover{color:var(--gold)}
.cta-band{background:rgba(11,196,180,.07);border:1px solid rgba(11,196,180,.2);border-radius:8px;padding:1.5rem;text-align:center;margin:2rem 0}
.cta-band h3{color:var(--teal);margin-bottom:.4rem}
.cta-band p{font-size:.9rem;margin-bottom:1rem}
.cta-btn{display:inline-block;background:var(--teal);color:#000 !important;font-weight:700;padding:.55rem 1.4rem;border-radius:5px;text-decoration:none !important;font-size:.88rem;letter-spacing:.05em}
.cta-btn:hover{background:#0ae0ce}
.breadcrumb{font-size:.8rem;color:var(--muted);margin-bottom:1.5rem}
.breadcrumb a{color:var(--muted)}
.breadcrumb a:hover{color:var(--gold)}
.main-layout{display:grid;grid-template-columns:1fr 300px;gap:2rem;padding:2rem 0}
.sidebar-card{background:var(--bg-card);border:1px solid var(--border);border-radius:8px;padding:1rem;margin-bottom:1rem;font-size:.82rem}
.sidebar-card h4{font-size:.78rem;letter-spacing:.1em;text-transform:uppercase;color:var(--gold);margin-bottom:.7rem}
.sidebar-stat{display:flex;justify-content:space-between;padding:.3rem 0;border-bottom:1px solid var(--border);color:var(--muted)}
.sidebar-stat:last-child{border:none}
.sidebar-stat strong{color:var(--text)}
.tier-badge{font-family:var(--display);font-size:2rem;font-weight:900;text-align:center;padding:.5rem;border-radius:6px}
.related-list{list-style:none;display:flex;flex-direction:column;gap:.35rem}
.related-list a{color:var(--muted);font-size:.82rem;padding:.2rem 0;border-bottom:1px solid rgba(255,255,255,.04)}
.related-list a:hover{color:var(--gold);text-decoration:none}
.patch-badge{display:inline-flex;align-items:center;gap:.3rem;background:rgba(11,196,180,.1);color:var(--teal);border:1px solid rgba(11,196,180,.25);border-radius:4px;padding:3px 10px;font-size:.72rem;font-weight:700;letter-spacing:.07em}
.site-footer{border-top:1px solid var(--border);padding:2rem 0;margin-top:3rem;text-align:center;color:var(--muted);font-size:.8rem}
.site-footer a{color:var(--muted)}
.matchup-intro strong{color:#fff}
.guide-section{margin-bottom:2rem}
.guide-section h2{font-size:1.2rem}
.tip-box{background:rgba(11,196,180,.07);border-left:3px solid var(--teal);border-radius:0 6px 6px 0;padding:.75rem 1rem;margin:1rem 0;font-size:.88rem}
.tip-box strong{color:var(--teal)}
@media(max-width:768px){
  .main-layout{grid-template-columns:1fr}
  .sidebar{order:-1}
  .counter-grid,.synergy-grid{grid-template-columns:repeat(auto-fill,minmax(130px,1fr))}
}
"""

# ──────────────────────────────────────────────
# SHARED HTML PARTIALS
# ──────────────────────────────────────────────
def header():
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@700;900&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
"""

def site_header_html():
    return f"""<header class="site-header">
  <div class="inner">
    <a href="{BASE_URL}/" class="site-logo" style="text-decoration:none">
      Forge of Runeterra
      <span>LoL Builds & Tier Lists</span>
    </a>
    <nav class="header-nav">
      <a href="{BASE_URL}/champions/">Champions</a>
      <a href="{BASE_URL}/#tierlist">Tier List</a>
      <a href="{BASE_URL}/#builds">Builds</a>
      <a href="{BASE_URL}/#guides">Guides</a>
      <a href="{BASE_URL}/patch/{PATCH.replace('.', '-')}/">Patch {PATCH}</a>
    </nav>
    <a href="{BASE_URL}/" class="launch-btn">▶ Open Full App</a>
  </div>
</header>
"""

def site_footer_html():
    return f"""<footer class="site-footer">
  <div class="container">
    <p>Forge of Runeterra is not affiliated with Riot Games. Data sourced from the Riot Games Data Dragon API.</p>
    <p style="margin-top:.4rem">
      <a href="{BASE_URL}/">Home</a> &bull;
      <a href="{BASE_URL}/champions/">All Champions</a> &bull;
      <a href="{BASE_URL}/patch/{PATCH.replace('.', '-')}/">Patch {PATCH}</a> &bull;
      <a href="{BASE_URL}/sitemap.xml">Sitemap</a>
    </p>
    <p style="margin-top:.4rem">Patch {PATCH} &bull; {PATCH_DATE}</p>
  </div>
</footer>
"""

def styles():
    return f"<style>{CSS}</style>"

# ──────────────────────────────────────────────
# CHAMPION SLAB PAGE
# ──────────────────────────────────────────────
def champion_schema(c):
    return json.dumps([
      {
        "@context": "https://schema.org",
        "@type": "TechArticle",
        "headline": f"{c['name']} Build Guide — Patch {PATCH} | Forge of Runeterra",
        "description": f"Best {c['name']} build for Patch {PATCH}: items, runes, counters, and playstyle guide. {c['name']} is {c['title']}, a {role_label(c['primary_role'])} champion.",
        "datePublished": PATCH_DATE,
        "dateModified": PATCH_DATE,
        "author": {"@type": "Organization","name": "Forge of Runeterra"},
        "publisher": {"@type": "Organization","name": "Forge of Runeterra","url": BASE_URL},
        "url": f"{BASE_URL}/champions/{c['slug']}/",
        "about": {
          "@type": "VideoGame",
          "name": "League of Legends",
          "gamePlatform": "PC"
        },
        "keywords": f"{c['name']} build, {c['name']} runes, {c['name']} counters, {c['name']} guide, {c['name']} Patch {PATCH}, {role_label(c['primary_role'])} tier list, League of Legends {c['name']}"
      },
      {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
          {
            "@type": "Question",
            "name": f"What is the best build for {c['name']} in Patch {PATCH}?",
            "acceptedAnswer": {
              "@type": "Answer",
              "text": f"The recommended {c['name']} build for Patch {PATCH} starts with {c['items'][0] if c['items'] else 'a mythic item'} and builds into {', '.join(c['items'][1:4]) if len(c['items']) > 1 else 'core items'}. {c['name']} is a {c['build_type']} champion who benefits most from this item path."
            }
          },
          {
            "@type": "Question",
            "name": f"What runes should I use on {c['name']}?",
            "acceptedAnswer": {
              "@type": "Answer",
              "text": f"Run {c['runes'].get('name','Conqueror')} as your keystone on the {c['runes'].get('path','Precision')} path. Primary rune slots: {', '.join(c['runes'].get('slots',[]))}. Secondary tree: {c['runes'].get('secondary','Resolve')} with {', '.join(c['runes'].get('secSlots',[]))}."
            }
          },
          {
            "@type": "Question",
            "name": f"What counters {c['name']}?",
            "acceptedAnswer": {
              "@type": "Answer",
              "text": f"Champions that consistently counter {c['name']} include {', '.join(c['counters'][:3]) if c['counters'] else 'strong lane bullies'}. These picks exploit {c['name']}\\'s weaknesses in laning phase or teamfights."
            }
          },
          {
            "@type": "Question",
            "name": f"What lane does {c['name']} play?",
            "acceptedAnswer": {
              "@type": "Answer",
              "text": f"{c['name']} primarily plays {role_label(c['primary_role'])}. {('They can also flex to ' + ', '.join(role_label(r) for r in c['secondary_roles']) + '.') if c['secondary_roles'] else 'They have limited flex potential outside their primary role.'}"
            }
          }
        ]
      }
    ], indent=2)

def champion_page(c):
    tier_class = f"tier-{c['tier']}"
    items_html = ''.join(
        f'<div class="item-chip"><img src="{item_img(item)}" alt="{item}" loading="lazy" onerror="this.src=\'{DD_CDN}/item/3364.png\'">{item}</div>'
        for item in c['items']
    )
    runes = c['runes']
    rune_slots_html = ''.join(f'<span class="rune-chip">{s}</span>' for s in runes.get('slots', []))
    rune_sec_html   = ''.join(f'<span class="rune-chip">{s}</span>' for s in runes.get('secSlots', []))
    rune_shards_html= ''.join(f'<span class="shard-chip">{s}</span>' for s in runes.get('shards', []))

    counters_html = ''.join(
        f'<div class="counter-card"><img src="{img(CHAMPS[n]["id"] if n in CHAMPS else n.lower())}" alt="{n}" loading="lazy" onerror="this.style.display=\'none\'"><a href="{BASE_URL}/champions/{CHAMPS[n]["slug"] if n in CHAMPS else n.lower()}/">{n}</a></div>'
        for n in c['counters'][:5]
    )

    # Synergies: same role + build type complementary picks
    same_role = [ch for ch in CHAMPS.values()
                 if ch['primary_role'] != c['primary_role'] and ch['name'] != c['name']][:5]
    synergies_html = ''.join(
        f'<div class="synergy-card"><img src="{img(ch["id"])}" alt="{ch["name"]}" loading="lazy" onerror="this.style.display=\'none\'"><a href="{BASE_URL}/champions/{ch["slug"]}/">{ch["name"]}</a></div>'
        for ch in same_role[:5]
    )

    related_champs = [ch for ch in CHAMPS.values()
                      if ch['primary_role'] == c['primary_role'] and ch['name'] != c['name']][:8]
    related_html = ''.join(
        f'<li><a href="{BASE_URL}/champions/{ch["slug"]}/">{ch["name"]}</a> — {ch["title"]}</li>'
        for ch in related_champs
    )

    # Matchup links (counter pages)
    matchup_links_html = ''.join(
        f'<li><a href="{BASE_URL}/counters/{c["slug"]}-vs-{CHAMPS[n]["slug"] if n in CHAMPS else n.lower()}/">{c["name"]} vs {n}</a> — matchup guide</li>'
        for n in c['counters'][:5] if n in CHAMPS
    )

    overview = c['overview'] or c['playstyle'] or f"{c['name']} is a {c['build_type']} champion who plays {role_label(c['primary_role'])}."
    sec_lanes_txt = (
        f"Common secondary: {', '.join(role_label(r) for r in c['secondary_roles'])}."
        if c['secondary_roles'] else
        f"{c['name']} is a dedicated {role_label(c['primary_role'])} specialist with limited flex potential."
    )

    return f"""{header()}
<title>{c['name']} Build, Runes & Guide — Patch {PATCH} | Forge of Runeterra</title>
<meta name="description" content="Best {c['name']} build for Patch {PATCH}: {c['items'][0] if c['items'] else 'optimal items'}, {runes.get('name','keystone')}, counters, and playstyle guide. {c['name']} is {c['title']}.">
<meta name="keywords" content="{c['name']} build, {c['name']} runes, {c['name']} counters, {c['name']} guide, {c['name']} Patch {PATCH}, best {c['name']} build Season 2">
<link rel="canonical" href="{BASE_URL}/champions/{c['slug']}/">
<meta property="og:title" content="{c['name']} Build & Guide — Patch {PATCH}">
<meta property="og:description" content="Best {c['name']} build for Patch {PATCH}: items, runes, counters, and playstyle. Updated {PATCH_DATE}.">
<meta property="og:image" content="{img(c['id'])}">
<meta property="og:url" content="{BASE_URL}/champions/{c['slug']}/">
<meta property="og:type" content="article">
<meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">{champion_schema(c)}</script>
{styles()}
</head>
<body>
{site_header_html()}
<main>
<div class="container">
  <div class="hero">
    <div class="breadcrumb">
      <a href="{BASE_URL}/">Home</a> &rsaquo; <a href="{BASE_URL}/champions/">Champions</a> &rsaquo; {c['name']}
    </div>
    <div class="champ-hero">
      <img class="champ-splash" src="{img(c['id'])}" alt="{c['name']}" loading="eager" onerror="this.style.opacity='.3'">
      <div class="champ-meta">
        <h1>{c['name']}</h1>
        <p class="champ-subtitle">{c['title']}</p>
        <div class="tags">
          {''.join(f'<span class="tag">{t}</span>' for t in c['tags'])}
          <span class="tag role">{role_label(c['primary_role'])}</span>
          <span class="tag tier-{c['tier']}">{c['tier']} Tier</span>
          <span class="patch-badge">Patch {PATCH}</span>
        </div>
      </div>
    </div>
  </div>

  <div class="main-layout">
    <div class="main-col">

      <!-- ═══ 1. WHAT IS THE BEST BUILD ═══ -->
      <section class="panel">
        <div class="panel-header">🗡 Best {c['name']} Build — Patch {PATCH}</div>
        <div class="panel-body">
          <div class="answer-first">
            <strong>The best {c['name']} build for Patch {PATCH} runs {c['items'][0] if c['items'] else 'a standard mythic'} as the core mythic, building into {', '.join(c['items'][1:3]) if len(c['items'])>1 else 'core power items'}.</strong>
            <p>This build maximizes {c['name']}'s {c['build_type'].lower()} strengths. Full item path:</p>
          </div>
          <div class="items-grid">{items_html}</div>
        </div>
      </section>

      <!-- ═══ 2. WHAT RUNES ═══ -->
      <section class="panel">
        <div class="panel-header">✦ Recommended Runes — Patch {PATCH}</div>
        <div class="panel-body">
          <div class="answer-first">
            <strong>Run <em>{runes.get("name","Conqueror")}</em> on the {runes.get("path","Precision")} path. Secondary tree: {runes.get("secondary","Resolve")}.</strong>
          </div>
          <div class="rune-block">
            <div class="rune-keystone">⬟ {runes.get("name","Conqueror")} <span style="font-size:.7rem;font-weight:400;color:var(--muted)">— Keystone</span></div>
            <div class="rune-tree-label">{runes.get("path","Precision")} Path</div>
            <div class="rune-chips">{rune_slots_html}</div>
            <div class="rune-tree-label">{runes.get("secondary","Resolve")} Secondary</div>
            <div class="rune-chips">{rune_sec_html}</div>
            <div class="rune-tree-label">Stat Shards</div>
            <div class="rune-chips">{rune_shards_html}</div>
          </div>
        </div>
      </section>

      <!-- ═══ 3. WHAT LANE / PLAYSTYLE ═══ -->
      <section class="panel">
        <div class="panel-header">🗺 Lane Priority &amp; Playstyle</div>
        <div class="panel-body">
          <div class="answer-first">
            <strong>{c['name']} is a {role_label(c['primary_role'])} champion. {sec_lanes_txt}</strong>
            <p>{overview}</p>
          </div>

          <h3>How to play {c['name']} in Patch {PATCH}</h3>

          <h3>Early Game (Levels 1–6)</h3>
          <p>Focus on learning {c['name']}'s core ability combo and last-hitting efficiently. Your first item spike at 1,300–1,600 gold is your first power window. Play safe until level 6 unless you have a clear trading advantage.</p>

          <h3>Mid Game (Items 1–2)</h3>
          <p>After your first completed item, look to make plays. {c['name']} transitions well into roaming or side-lane pressure depending on your game state. Track the enemy jungler and contest objectives around Dragon and Herald.</p>

          <h3>Late Game (Full Build)</h3>
          <p>At full build, {c['name']} is a {c['tier']}-tier teamfight presence. Identify your win condition — if you're ahead, force fights. If you're behind, play for picks and objective trades rather than even teamfights.</p>
        </div>
      </section>

      <!-- ═══ 4. WHAT COUNTERS ═══ -->
      <section class="panel">
        <div class="panel-header">⚔ {c['name']} Counters &amp; Hard Matchups</div>
        <div class="panel-body">
          <div class="answer-first">
            <strong>The strongest counters to {c['name']} in Patch {PATCH} are champions that exploit their {c['build_type'].lower()} weaknesses.</strong>
          </div>
          <div class="counter-grid">{counters_html}</div>
          <h3>How to play against {c['name']}</h3>
          <p>Against {c['name']}, prioritize denying their early item timing. Avoid extended trades if they have their full rune set active. Ward against their jungler and track their roam windows carefully.</p>
          <div class="tip-box">
            <strong>Pro tip:</strong> {c['name']}'s power spikes dramatically after their first item. Play aggressive before 1,300 gold if you're an early-game champion, or play safe and scale if you out-scale them.
          </div>
          {'<ul class="related-list" style="margin-top:1rem">' + matchup_links_html + '</ul>' if matchup_links_html else ''}
        </div>
      </section>

      <!-- ═══ 5. SYNERGIES ═══ -->
      <section class="panel">
        <div class="panel-header">✦ Best Synergies with {c['name']}</div>
        <div class="panel-body">
          <div class="answer-first">
            <strong>{c['name']} pairs best with champions that cover their weaknesses and enable their strengths in the current meta.</strong>
          </div>
          <div class="synergy-grid">{synergies_html}</div>
        </div>
      </section>

      <!-- ═══ 6. PATCH HISTORY ═══ -->
      <section class="panel">
        <div class="panel-header">📋 Patch History — Recent Changes</div>
        <div class="panel-body">
          <div class="answer-first">
            <strong>In Patch {PATCH}, {c['name']} received {'targeted balance adjustments keeping them at ' + c['tier'] + '-tier' if c['tier'] in ['S','A'] else 'no significant changes, maintaining their ' + c['tier'] + '-tier status'}.</strong>
          </div>
          <p>Current tier: <strong>{c['tier']}</strong>. This reflects {c['name']}'s standing in the Patch {PATCH} meta across all skill levels. Check the <a href="{BASE_URL}/patch/{PATCH.replace('.', '-')}/">full Patch {PATCH} notes</a> for specific numbers.</p>
        </div>
      </section>

      <!-- ═══ CTA ═══ -->
      <div class="cta-band">
        <h3>Want live champion select overlay stats?</h3>
        <p>Forge of Runeterra's interactive tool shows real-time builds, runes, and counter picks in champion select.</p>
        <a href="{BASE_URL}/?champion={c['id']}" class="cta-btn">Open {c['name']} in Full App →</a>
      </div>

    </div><!-- /main-col -->

    <aside class="sidebar">
      <!-- Quick Stats -->
      <div class="sidebar-card">
        <h4>Quick Stats — Patch {PATCH}</h4>
        <div class="tier-badge tier-{c['tier']}">{c['tier']}</div>
        <div style="text-align:center;font-size:.7rem;color:var(--muted);margin-bottom:.75rem">Current Tier</div>
        <div class="sidebar-stat"><span>Primary Role</span><strong>{role_label(c['primary_role'])}</strong></div>
        <div class="sidebar-stat"><span>Build Type</span><strong>{c['build_type']}</strong></div>
        <div class="sidebar-stat"><span>Keystone</span><strong>{runes.get('name','—')}</strong></div>
        <div class="sidebar-stat"><span>First Item</span><strong>{c['items'][0] if c['items'] else '—'}</strong></div>
      </div>

      <!-- Same-role champions -->
      <div class="sidebar-card">
        <h4>Other {role_label(c['primary_role'])} Champions</h4>
        <ul class="related-list">{related_html}</ul>
      </div>

      <!-- Back to site -->
      <div class="sidebar-card" style="text-align:center">
        <a href="{BASE_URL}/" class="cta-btn" style="display:block;padding:.65rem">← All Champions</a>
      </div>
    </aside>
  </div>
</div>
</main>
{site_footer_html()}
</body></html>"""

# ──────────────────────────────────────────────
# COUNTER / MATCHUP PAGE
# ──────────────────────────────────────────────
def counter_page(c1, c2):
    """Generate a matchup page: c1 vs c2."""
    overview1 = c1['overview'] or f"{c1['name']} is a {c1['build_type']} champion."
    overview2 = c2['overview'] or f"{c2['name']} is a {c2['build_type']} champion."

    schema = json.dumps({
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": f"{c1['name']} vs {c2['name']} Matchup Guide — Patch {PATCH}",
        "description": f"How to beat {c2['name']} as {c1['name']} in Patch {PATCH}. Tips, item adjustments, and lane strategy.",
        "datePublished": PATCH_DATE,
        "author": {"@type": "Organization", "name": "Forge of Runeterra"},
        "url": f"{BASE_URL}/counters/{c1['slug']}-vs-{c2['slug']}/",
    }, indent=2)

    return f"""{header()}
<title>{c1['name']} vs {c2['name']} Matchup — Patch {PATCH} | Forge of Runeterra</title>
<meta name="description" content="How to play {c1['name']} into {c2['name']} in Patch {PATCH}. Win the {c1['name']} vs {c2['name']} matchup with itemization tips, rune adjustments, and lane strategy.">
<link rel="canonical" href="{BASE_URL}/counters/{c1['slug']}-vs-{c2['slug']}/">
<meta property="og:title" content="{c1['name']} vs {c2['name']} — Matchup Guide Patch {PATCH}">
<meta property="og:url" content="{BASE_URL}/counters/{c1['slug']}-vs-{c2['slug']}/">
<script type="application/ld+json">{schema}</script>
{styles()}
</head>
<body>
{site_header_html()}
<main>
<div class="container">
  <div class="breadcrumb" style="margin-top:1.5rem">
    <a href="{BASE_URL}/">Home</a> &rsaquo;
    <a href="{BASE_URL}/champions/{c1['slug']}/">{c1['name']}</a> &rsaquo;
    {c1['name']} vs {c2['name']}
  </div>

  <!-- Matchup header -->
  <div style="display:flex;align-items:center;gap:1rem;flex-wrap:wrap;margin:1rem 0 2rem">
    <img src="{img(c1['id'])}" alt="{c1['name']}" style="width:72px;height:72px;border-radius:8px;border:2px solid var(--border)">
    <div style="font-family:var(--display);font-size:2rem;color:var(--muted);padding:0 .5rem">VS</div>
    <img src="{img(c2['id'])}" alt="{c2['name']}" style="width:72px;height:72px;border-radius:8px;border:2px solid var(--border)">
    <div>
      <h1 style="font-size:1.6rem">{c1['name']} vs {c2['name']}</h1>
      <div style="font-size:.82rem;color:var(--muted)">{role_label(c1['primary_role'])} Matchup &bull; Patch {PATCH}</div>
    </div>
  </div>

  <!-- Answer-first block -->
  <div class="panel">
    <div class="panel-header">⚔ How to Beat {c2['name']} as {c1['name']}</div>
    <div class="panel-body">
      <div class="answer-first">
        <strong>To win {c1['name']} vs {c2['name']} in Patch {PATCH}, exploit {c2['name']}'s {c2['build_type'].lower()} vulnerabilities by itemizing early resistance and denying their power spike timing.</strong>
        <p>{c1['name']} ({c1['build_type']}) against {c2['name']} ({c2['build_type']}) is a matchup that depends heavily on level timing, summoner spell cooldowns, and the jungler's ganking priority for {role_label(c1['primary_role'])}.</p>
      </div>

      <h2>What makes this matchup difficult</h2>
      <p>{c2['name']} presents a challenge for {c1['name']} primarily because of their {c2['build_type'].lower()} toolkit. Understanding their key ability cooldowns and power windows is essential to navigating this lane.</p>

      <h2>How {c1['name']} wins this matchup</h2>
      <p>{overview1}</p>
      <div class="tip-box">
        <strong>Key tip:</strong> Against {c2['name']}, prioritize your first item spike. At {c1['items'][0] if c1['items'] else 'your core item'}, your trading power increases significantly. Force short trades before level 6 if you're an early-game champion.
      </div>

      <h2>Item adjustments for this matchup</h2>
      <p>Your standard {c1['name']} build ({c1['items'][0] if c1['items'] else 'core mythic'}) applies here, but consider adjusting your third item slot based on how dominant {c2['name']} is in the game.</p>
      <div class="items-grid">
        {''.join(f'<div class="item-chip"><img src="{item_img(item)}" alt="{item}" loading="lazy" onerror="this.src=\'{DD_CDN}/item/3364.png\'">{item}</div>' for item in c1["items"][:4])}
      </div>

      <h2>About your opponent: {c2['name']}</h2>
      <p>{overview2}</p>

      <h2>Frequently asked: {c1['name']} vs {c2['name']}</h2>

      <h3>Does {c1['name']} counter {c2['name']}?</h3>
      <p><strong>{c1['name']} {'has favourable matchup tools against' if c2['name'] in c1['counters'] else 'does not naturally hard-counter'} {c2['name']}.</strong> Matchup outcomes depend on player execution, item timing, and jungle priority as much as pure champion kit interactions.</p>

      <h3>What level does {c1['name']} win this lane?</h3>
      <p><strong>The first notable power window for {c1['name']} is levels 3 and 6.</strong> At level 3 you have access to your full basic combo. At level 6 your ultimate opens new all-in or escape options depending on your champion archetype.</p>

      <h3>What summoner spells should I run?</h3>
      <p><strong>Flash is non-negotiable. Your second summoner depends on your matchup.</strong> Against aggressive {c2['name']} players, Ignite secures kills in winning trades. Against scaling or defensive opponents, Teleport provides map-wide presence.</p>
    </div>
  </div>

  <div style="display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin-top:1rem;flex-wrap:wrap">
    <a href="{BASE_URL}/champions/{c1['slug']}/" class="cta-btn" style="text-align:center;padding:.7rem">Full {c1['name']} Guide →</a>
    <a href="{BASE_URL}/champions/{c2['slug']}/" class="cta-btn" style="text-align:center;padding:.7rem;background:rgba(255,255,255,.1);color:var(--text)">Full {c2['name']} Guide →</a>
  </div>
</div>
</main>
{site_footer_html()}
</body></html>"""

# ──────────────────────────────────────────────
# META GUIDE PAGE (per role)
# ──────────────────────────────────────────────
ROLE_GUIDES = {
    'top':     ('Best Top Lane Champions', 'Top lane carries and bruisers'),
    'jungle':  ('Best Jungle Champions', 'Jungle tier list and meta picks'),
    'mid':     ('Best Mid Lane Champions', 'Mid lane mages and assassins'),
    'adc':     ('Best ADC Champions', 'Bot lane marksman tier list'),
    'support': ('Best Support Champions', 'Support meta picks and builds'),
}

def meta_guide_page(role):
    title, subtitle = ROLE_GUIDES[role]
    role_champs = sorted(
        [c for c in CHAMPS.values() if c['primary_role'] == role],
        key=lambda c: ['S','A','B','C','D'].index(c['tier']) if c['tier'] in ['S','A','B','C','D'] else 4
    )
    s_tier = [c for c in role_champs if c['tier'] == 'S']
    a_tier = [c for c in role_champs if c['tier'] == 'A']
    b_tier = [c for c in role_champs if c['tier'] == 'B']

    def tier_section(tier_name, champs_list, color):
        if not champs_list:
            return ''
        cards = ''.join(
            f'<a href="{BASE_URL}/champions/{c["slug"]}/" style="display:flex;align-items:center;gap:.6rem;background:rgba(255,255,255,.04);border:1px solid var(--border);border-radius:5px;padding:.5rem .7rem;text-decoration:none;color:var(--text)">'
            f'<img src="{img(c["id"])}" alt="{c["name"]}" width="36" height="36" style="border-radius:4px;object-fit:cover" loading="lazy">'
            f'<div><div style="font-weight:600;font-size:.85rem">{c["name"]}</div>'
            f'<div style="font-size:.7rem;color:var(--muted)">{c["build_type"]}</div></div>'
            f'</a>'
            for c in champs_list
        )
        return f'<h3 style="color:{color}">{tier_name} Tier</h3><div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:.5rem;margin-bottom:1.5rem">{cards}</div>'

    schema = json.dumps({
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": f"Best {role_label(role)} Champions Patch {PATCH} — {title}",
        "description": f"Complete {role_label(role)} tier list for Patch {PATCH}. Best picks, meta analysis, and why each champion is ranked.",
        "datePublished": PATCH_DATE,
        "dateModified": PATCH_DATE,
        "author": {"@type": "Organization", "name": "Forge of Runeterra"},
        "url": f"{BASE_URL}/guides/best-{role}-patch-{PATCH.replace('.', '-')}/",
    }, indent=2)

    return f"""{header()}
<title>Best {role_label(role)} Champions Patch {PATCH} | Forge of Runeterra</title>
<meta name="description" content="Best {role_label(role)} champions for Patch {PATCH}. S-tier: {', '.join(c['name'] for c in s_tier[:4])}. Complete tier list with explanations for why each pick is ranked.">
<link rel="canonical" href="{BASE_URL}/guides/best-{role}-patch-{PATCH.replace('.', '-')}/">
<meta property="og:title" content="Best {role_label(role)} Champions — Patch {PATCH}">
<meta property="og:url" content="{BASE_URL}/guides/best-{role}-patch-{PATCH.replace('.', '-')}/">
<script type="application/ld+json">{schema}</script>
{styles()}
</head>
<body>
{site_header_html()}
<main>
<div class="container" style="padding-top:2rem">
  <div class="breadcrumb">
    <a href="{BASE_URL}/">Home</a> &rsaquo;
    <a href="{BASE_URL}/guides/">Guides</a> &rsaquo;
    Best {role_label(role)} — Patch {PATCH}
  </div>
  <h1>Best {role_label(role)} Champions — Patch {PATCH}</h1>
  <div class="tags" style="margin-bottom:1.5rem">
    <span class="patch-badge">Patch {PATCH}</span>
    <span class="tag role">{role_label(role)}</span>
    <span class="tag">Updated {PATCH_DATE}</span>
  </div>

  <div class="panel">
    <div class="panel-header">📊 {role_label(role)} Tier List — Patch {PATCH}</div>
    <div class="panel-body">
      <div class="answer-first">
        <strong>The best {role_label(role)} champions in Patch {PATCH} are {', '.join(c['name'] for c in s_tier[:3])}{', and more' if len(s_tier) > 3 else ''} — all offering dominant win conditions in the current meta.</strong>
        <p>This tier list reflects Patch {PATCH}'s balance changes and the current competitive meta. S-tier means playable and strong at all skill levels; A-tier means strong in the right hands; B-tier means solid but requires good matchup knowledge.</p>
      </div>
      {tier_section('S', s_tier, '#ffd700')}
      {tier_section('A', a_tier, '#e74c3c')}
      {tier_section('B', b_tier, '#3498db')}
    </div>
  </div>

  <div class="panel">
    <div class="panel-header">🔍 Why these champions are strong in Patch {PATCH}</div>
    <div class="panel-body">
      <h2>What changed for {role_label(role)} in Patch {PATCH}?</h2>
      <p><strong>Patch {PATCH} shifted the {role_label(role)} meta with targeted buffs and nerfs that reshuffled tier placements.</strong> The champions that benefited most are those whose item paths or ability scalings interact with the patch's systemic changes.</p>

      <h2>How to climb ranked as {role_label(role)} in Season 2</h2>
      <p><strong>Pick two or three champions from the S or A tier and focus on mastering their matchups rather than playing a large champion pool.</strong> Consistency outperforms flexibility at most elo ranges — knowing your champion's exact power spikes and item timing creates more wins than playing the newest "OP" pick on day one.</p>

      <div class="tip-box">
        <strong>Meta insight:</strong> The current {role_label(role)} meta rewards champions with strong first-item power spikes. If your champion's first item costs 1,300–1,600 gold and opens meaningful fighting windows, you're in a good position.
      </div>

      <h2>Best {role_label(role)} champion for beginners in Patch {PATCH}</h2>
      <p><strong>{'Garen for top, Warwick for jungle, Annie for mid, Miss Fortune for ADC, and Soraka for support are the lowest mechanical floors in each role.' if role == 'all' else f"For new {role_label(role)} players in Patch {PATCH}, start with a champion whose kit has a clear, repeatable win condition and doesn't rely on difficult mechanics."}</strong></p>

      {''.join(f"<h2>Why is {c['name']} S-tier in Patch {PATCH}?</h2><p><strong>{c['name']} earns S-tier because of {c['build_type'].lower()} dominance with a reliable first-item power spike.</strong> {c['overview'][:200] + ('...' if len(c['overview']) > 200 else '')}</p>" for c in s_tier[:3])}
    </div>
  </div>

  <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:.7rem;margin:1.5rem 0">
    {''.join(f'<a href="{BASE_URL}/guides/best-{r}-patch-{PATCH.replace(chr(46), chr(45))}/" class="cta-btn" style="text-align:center;padding:.6rem;{"" if r == role else "background:rgba(255,255,255,.08);color:var(--text)"}">{role_label(r)}</a>' for r in ["top","jungle","mid","adc","support"])}
  </div>

  <div class="cta-band">
    <h3>See the full interactive tier list</h3>
    <p>Filter by role, sort by win rate, and explore every champion build in the full app.</p>
    <a href="{BASE_URL}/#tierlist" class="cta-btn">Open Tier List →</a>
  </div>
</div>
</main>
{site_footer_html()}
</body></html>"""

# ──────────────────────────────────────────────
# PATCH PAGE
# ──────────────────────────────────────────────
PATCH_DATA = {
    'buffs': [
        {'name':'LeBlanc','change':'W cooldown reduced; base damage increased','builds_affected':'Mage','why':'LeBlanc\'s W was the main limiter on her early-game burst pattern. This restores her as a reliable mid-lane carry into melee matchups.'},
        {'name':'Draven','change':'Q cooldown reduced from 18-14s to 16-12s','builds_affected':'ADC','why':'Shorter Spinning Axe downtime directly increases his sustained damage output and lane aggression windows.'},
        {'name':"Kai'Sa",'change':'E cooldown reduced at early ranks','builds_affected':'ADC','why':'Faster poke and engage pattern makes her more competitive against longer-range ADCs in lane.'},
        {'name':'Olaf','change':'W jungle-camp bonus damage increased','builds_affected':'Fighter','why':'Opens Olaf as a viable jungle option without compromising his top-lane identity.'},
        {'name':'Poppy','change':'W jungle-clear damage cap raised','builds_affected':'Tank','why':'Makes tank Poppy jungle a legitimate flex option in coordinated compositions.'},
        {'name':'Aphelios','change':'Passive mark damage scaling up from 10% to 15% bonus AD','builds_affected':'ADC','why':'A meaningful late-game power increase that rewards high-AD builds and prolongs his relevance into MSI.'},
    ],
    'nerfs': [
        {'name':'Senna','change':'Soul drop chance on kill: 10%→5%; damage reduction adjusted','builds_affected':'ADC/Support','why':'Senna was too efficient at both farming souls and tanking damage. This forces a clearer build and role commitment.'},
        {'name':'Bard','change':'Meep damage reduced','builds_affected':'Support','why':'Bard\'s tank-roam playstyle was providing too much all-round value without a clear weakness.'},
        {'name':'Brand','change':'Passive detonation damage reduced at early levels','builds_affected':'Mage/Support','why':'Early game dominance in bot lane was suppressing too much ADC agency in the 2v2 phase.'},
        {'name':'Cassiopeia','change':'Base health reduced','builds_affected':'Mage','why':'Targeted at her laning durability, preserving late-game scaling while creating exploitable early windows.'},
        {'name':"K'Sante",'change':'Physical damage and true damage on Path Maker reduced','builds_affected':'Tank','why':'Consistent overperformance in competitive play at high elo.'},
        {'name':"Rek'Sai",'change':'Burst damage in extended fights reduced','builds_affected':'Fighter','why':'Season 2 jungle dominance warranted reduction without removing her early-game identity.'},
    ],
    'new': [
        {'name':'Locke','change':'New champion released','builds_affected':'Mage','why':'Locke is the Ashen Exorcist — an on-hit mid-lane mage who marks enemies with Soul Nails.'},
    ],
    'systems': [
        {'name':'Last Hit Indicators','change':'Now enabled in Normal Draft and Ranked SR','why':'Previously only in Swiftplay and Co-op. The white indicator on a minion\'s health bar helps new players land last hits more consistently.'},
        {'name':'Imperial Mandate','change':'Build path reworked: now Amp Tome × 2 + Bandleglass Mirror','why':'Smoother component route for support players who found the old Blasting Wand path awkward to navigate.'},
    ]
}

def patch_page():
    # Pre-compute buff/nerf summary links to avoid nested f-string issues
    def get_slug(champ_name):
        clean = champ_name.replace("'","").replace(" ","")
        if clean in CHAMPS: return CHAMPS[clean]['slug']
        if champ_name in CHAMPS: return CHAMPS[champ_name]['slug']
        return '#'

    buff_links = ''.join(
        f'<div style="padding:.2rem 0;color:var(--text);font-size:.85rem">• '
        f'<a href="{BASE_URL}/champions/{get_slug(b["name"])}/">{b["name"]}</a></div>'
        for b in PATCH_DATA['buffs']
    )
    nerf_names = ''.join(
        f'<div style="padding:.2rem 0;color:var(--text);font-size:.85rem">• {n["name"]}</div>'
        for n in PATCH_DATA['nerfs']
    )
    schema = json.dumps({
        "@context": "https://schema.org",
        "@type": "TechArticle",
        "headline": f"League of Legends Patch {PATCH} Notes — Full Breakdown",
        "description": f"Complete Patch {PATCH} breakdown: all champion buffs, nerfs, new champion Locke, and system changes explained. Updated {PATCH_DATE}.",
        "datePublished": PATCH_DATE,
        "dateModified": PATCH_DATE,
        "author": {"@type": "Organization", "name": "Forge of Runeterra"},
        "url": f"{BASE_URL}/patch/{PATCH.replace('.', '-')}/",
        "about": {"@type": "VideoGame", "name": "League of Legends"},
        "keywords": f"Patch {PATCH}, League of Legends {PATCH}, patch notes {PATCH}, LoL patch {PATCH}, MSI 2026 patch, Locke champion"
    }, indent=2)

    buffs_html = ''.join(
        f"""<div class="panel" style="margin-bottom:1rem">
          <div class="panel-header" style="color:var(--green)">↑ {b['name']} Buffed</div>
          <div class="panel-body">
            <div class="answer-first">
              <strong>{b['name']}: {b['change']}.</strong>
              <p>{b['why']}</p>
            </div>
            <p style="font-size:.82rem;color:var(--muted)">Builds affected: {b['builds_affected']} &bull;
            <a href="{BASE_URL}/champions/{CHAMPS[b['name'].replace("'","")]['slug'] if b['name'].replace("'","") in CHAMPS else '#'}/">View {b['name']} build →</a></p>
          </div>
        </div>"""
        for b in PATCH_DATA['buffs']
    )

    nerfs_html = ''.join(
        f"""<div class="panel" style="margin-bottom:1rem">
          <div class="panel-header" style="color:var(--red)">↓ {n['name']} Nerfed</div>
          <div class="panel-body">
            <div class="answer-first">
              <strong>{n['name']}: {n['change']}.</strong>
              <p>{n['why']}</p>
            </div>
            <p style="font-size:.82rem;color:var(--muted)">Builds affected: {n['builds_affected']}</p>
          </div>
        </div>"""
        for n in PATCH_DATA['nerfs']
    )

    systems_html = ''.join(
        f"""<div style="padding:.75rem 0;border-bottom:1px solid var(--border)">
          <strong style="color:var(--gold)">{s['name']}</strong>
          <p style="font-size:.88rem;margin:.3rem 0 0">{s['change']}.</p>
          <p style="font-size:.82rem;color:var(--muted);margin:.3rem 0 0">{s['why']}</p>
        </div>"""
        for s in PATCH_DATA['systems']
    )

    return f"""{header()}
<title>League of Legends Patch {PATCH} Notes — Full Breakdown | Forge of Runeterra</title>
<meta name="description" content="Patch {PATCH} breakdown: Locke new champion, LeBlanc/Draven/Kai'Sa/Olaf/Poppy/Aphelios buffed, Senna/Bard/Brand/Cassiopeia/K'Sante/Rek'Sai nerfed. Imperial Mandate reworked. MSI 2026 prep patch.">
<link rel="canonical" href="{BASE_URL}/patch/{PATCH.replace('.', '-')}/">
<meta property="og:title" content="Patch {PATCH} Notes — Full Breakdown">
<meta property="og:url" content="{BASE_URL}/patch/{PATCH.replace('.', '-')}/">
<script type="application/ld+json">{schema}</script>
{styles()}
</head>
<body>
{site_header_html()}
<main>
<div class="container" style="padding-top:2rem">
  <div class="breadcrumb">
    <a href="{BASE_URL}/">Home</a> &rsaquo; Patch Notes &rsaquo; Patch {PATCH}
  </div>

  <div class="tags" style="margin:.5rem 0 1rem"><span class="patch-badge">Patch {PATCH}</span><span class="tag">Released {PATCH_DATE}</span><span class="tag">MSI 2026 Prep</span></div>
  <h1>League of Legends Patch {PATCH} — Full Breakdown</h1>
  <p style="font-size:1.05rem;color:#ccd6e8;margin-bottom:2rem">The final balance pass before MSI 2026. Locke joins the roster, Last Hit Indicators expand to ranked, and the support meta gets a meaningful shakeup.</p>

  <!-- HEADLINE SUMMARY -->
  <div class="panel">
    <div class="panel-header">📋 Patch {PATCH} Summary — 30-Second Overview</div>
    <div class="panel-body">
      <div class="answer-first">
        <strong>Patch {PATCH} buffed LeBlanc, Draven, Kai'Sa, Olaf, Poppy, and Aphelios; nerfed Senna, Bard, Brand, Cassiopeia, K'Sante, and Rek'Sai; and introduced Locke as a new mid-lane champion.</strong>
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin-top:1rem">
        <div>
          <div style="font-size:.72rem;text-transform:uppercase;letter-spacing:.1em;color:var(--green);margin-bottom:.4rem">↑ Buffed</div>
          {buff_links}
        </div>
        <div>
          <div style="font-size:.72rem;text-transform:uppercase;letter-spacing:.1em;color:var(--red);margin-bottom:.4rem">↓ Nerfed</div>
          {nerf_names}
        </div>
      </div>
    </div>
  </div>

  <!-- BUFFS -->
  <h2>Champion Buffs — Patch {PATCH}</h2>
  <p><strong>Six champions were buffed in Patch {PATCH}, all targeted at MSI 2026 competitive diversity.</strong> Each buff is explained below with its mechanical impact and which builds benefit most.</p>
  {buffs_html}

  <!-- NERFS -->
  <h2>Champion Nerfs — Patch {PATCH}</h2>
  <p><strong>Six champions received nerfs in Patch {PATCH}, primarily targeting supports and junglers that were overperforming across skill brackets.</strong></p>
  {nerfs_html}

  <!-- SYSTEMS -->
  <h2>System &amp; Item Changes — Patch {PATCH}</h2>
  <div class="panel">
    <div class="panel-body">{systems_html}</div>
  </div>

  <!-- NEW CHAMPION -->
  <h2>New Champion: Locke</h2>
  <div class="panel">
    <div class="panel-header">⭐ New Champion — Locke, the Ashen Exorcist</div>
    <div class="panel-body">
      <div class="answer-first">
        <strong>Locke is a new mid-lane on-hit mage who marks enemies with Soul Nails, rewarding sustained ability and auto-attack combinations over pure burst.</strong>
      </div>
      <p>Locke debuts in Patch {PATCH} as a Broken Covenant skin launch champion. Expect a 1–2 week adjustment period before their optimal build and tier placement stabilise. Early indications place Locke in the Mage build archetype with on-hit elements.</p>
      <div class="tip-box"><strong>New champion note:</strong> Avoid ranking Locke in your champion pool until Patch {PATCH} + 1 when the community has established their optimal build path. Release patches often see overtuned numbers that get hotfixed.</div>
    </div>
  </div>

  <!-- WHAT THIS MEANS -->
  <h2>What does Patch {PATCH} mean for ranked?</h2>
  <div class="panel">
    <div class="panel-body">
      <div class="answer-first">
        <strong>For ranked climbing in Patch {PATCH}, prioritise the buffed carries (LeBlanc, Draven, Kai'Sa, Aphelios) and avoid the nerfed supports (Senna, Bard, Brand) until their new tier placements stabilise.</strong>
      </div>
      <p>The MSI 2026 meta will tighten around whatever survives this patch. Expect professional teams to test the buffed Aphelios and LeBlanc aggressively. In solo queue, the Senna nerfs open up the support role for other enchanters and engage champions that had been crowded out.</p>
    </div>
  </div>

  <div class="cta-band">
    <h3>See updated tier lists and builds</h3>
    <p>All builds and tier placements have been updated for Patch {PATCH}.</p>
    <a href="{BASE_URL}/" class="cta-btn">Open Forge of Runeterra →</a>
  </div>
</div>
</main>
{site_footer_html()}
</body></html>"""

# ──────────────────────────────────────────────
# CHAMPIONS INDEX PAGE
# ──────────────────────────────────────────────
def champions_index_page():
    by_role = {'top':[],'jungle':[],'mid':[],'adc':[],'support':[]}
    for c in CHAMPS.values():
        r = c['primary_role']
        if r in by_role:
            by_role[r].append(c)

    def role_grid(role):
        champs = sorted(by_role[role], key=lambda c: ['S','A','B','C','D'].index(c['tier']) if c['tier'] in ['S','A','B','C','D'] else 4)
        cards = ''.join(
            f'<a href="{BASE_URL}/champions/{c["slug"]}/" style="display:flex;flex-direction:column;align-items:center;gap:.4rem;text-decoration:none;padding:.7rem;background:rgba(255,255,255,.04);border:1px solid var(--border);border-radius:6px;text-align:center">'
            f'<img src="{img(c["id"])}" alt="{c["name"]}" width="48" height="48" style="border-radius:6px;object-fit:cover" loading="lazy">'
            f'<div style="font-size:.82rem;color:var(--text);font-weight:600">{c["name"]}</div>'
            f'<div style="font-size:.65rem;color:var(--muted)">{c["tier"]}-Tier</div>'
            f'</a>'
            for c in champs
        )
        return f'<h2>{role_label(role)}</h2><div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(120px,1fr));gap:.5rem;margin-bottom:2rem">{cards}</div>'

    schema = json.dumps({
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": f"All League of Legends Champions — Patch {PATCH}",
        "description": f"Complete list of all {len(CHAMPS)} League of Legends champions with builds, runes, and tier rankings for Patch {PATCH}.",
        "url": f"{BASE_URL}/champions/",
    }, indent=2)

    return f"""{header()}
<title>All League of Legends Champions — Builds & Tier List Patch {PATCH} | Forge of Runeterra</title>
<meta name="description" content="All {len(CHAMPS)} League of Legends champions with optimal builds, rune pages, counters, and Patch {PATCH} tier rankings. Browse by role.">
<link rel="canonical" href="{BASE_URL}/champions/">
<script type="application/ld+json">{schema}</script>
{styles()}
</head>
<body>
{site_header_html()}
<main>
<div class="container" style="padding:2rem 0">
  <h1>All League of Legends Champions — Patch {PATCH}</h1>
  <p style="margin-bottom:1rem"><strong>Browse all {len(CHAMPS)} champions</strong> with builds, runes, counters, and tier rankings updated for Patch {PATCH}. Click any champion for their complete guide.</p>
  <div class="tags" style="margin-bottom:2rem">
    {''.join(f'<a href="{BASE_URL}/guides/best-{r}-patch-{PATCH.replace(chr(46), chr(45))}/" class="tag role" style="text-decoration:none">{role_label(r)}</a>' for r in ["top","jungle","mid","adc","support"])}
  </div>
  {''.join(role_grid(r) for r in ['top','jungle','mid','adc','support'])}
</div>
</main>
{site_footer_html()}
</body></html>"""

# ──────────────────────────────────────────────
# GUIDES INDEX
# ──────────────────────────────────────────────
def guides_index_page():
    return f"""{header()}
<title>League of Legends Guides — Tier Lists & Meta Guides Patch {PATCH} | Forge of Runeterra</title>
<meta name="description" content="LoL guides for Patch {PATCH}: best champions by role, meta tier lists, and patch breakdowns. Best ADC, jungle, mid, top, and support picks.">
<link rel="canonical" href="{BASE_URL}/guides/">
{styles()}
</head>
<body>
{site_header_html()}
<main>
<div class="container" style="padding:2rem 0">
  <h1>League of Legends Guides — Patch {PATCH}</h1>
  <p style="margin-bottom:2rem">Meta guides, tier lists, and patch analysis updated every two weeks.</p>

  <h2>Role Tier Lists — Patch {PATCH}</h2>
  <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:1rem;margin-bottom:2rem">
    {''.join(f'<a href="{BASE_URL}/guides/best-{r}-patch-{PATCH.replace(chr(46),chr(45))}/" style="display:block;background:var(--bg-card);border:1px solid var(--border);border-radius:8px;padding:1.2rem;text-decoration:none"><div style="font-family:var(--display);color:var(--gold);font-size:1rem;margin-bottom:.3rem">{role_label(r)}</div><div style="font-size:.8rem;color:var(--muted)">Best picks for Patch {PATCH}</div></a>' for r in ["top","jungle","mid","adc","support"])}
  </div>

  <h2>Patch Breakdowns</h2>
  <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:1rem">
    <a href="{BASE_URL}/patch/{PATCH.replace('.', '-')}/" style="display:block;background:var(--bg-card);border:1px solid rgba(11,196,180,.25);border-radius:8px;padding:1.2rem;text-decoration:none">
      <div style="font-family:var(--display);color:var(--teal);font-size:1rem;margin-bottom:.3rem">Patch {PATCH}</div>
      <div style="font-size:.8rem;color:var(--muted)">MSI 2026 prep — Locke, 6 buffs, 6 nerfs</div>
    </a>
  </div>
</div>
</main>
{site_footer_html()}
</body></html>"""

# ──────────────────────────────────────────────
# SITEMAP
# ──────────────────────────────────────────────
def generate_sitemap(generated_paths):
    urls = [f"""  <url>
    <loc>{BASE_URL}{path}</loc>
    <lastmod>{PATCH_DATE.replace(' ', '-')}</lastmod>
    <changefreq>{'weekly' if '/champions/' in path or '/patch/' in path else 'monthly'}</changefreq>
    <priority>{'0.9' if path in ['/', '/champions/', f'/patch/{PATCH.replace(chr(46), chr(45))}/'] else '0.8' if '/champions/' in path and path.count('/') == 3 else '0.6'}</priority>
  </url>""" for path in generated_paths]
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{chr(10).join(urls)}
</urlset>"""

# ──────────────────────────────────────────────
# ROBOTS.TXT
# ──────────────────────────────────────────────
def robots_txt():
    return f"""User-agent: *
Allow: /

User-agent: GPTBot
Allow: /

User-agent: Google-Extended
Allow: /

User-agent: anthropic-ai
Allow: /

User-agent: PerplexityBot
Allow: /

Sitemap: {BASE_URL}/sitemap.xml
"""

# ──────────────────────────────────────────────
# GENERATE ALL FILES
# ──────────────────────────────────────────────
def write(path, content):
    full = Path('site') / path.lstrip('/')
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(content, encoding='utf-8')

generated = ['/']

print("Building site structure...")

# 1. Champions index
write('champions/index.html', champions_index_page())
generated.append('/champions/')
print("  ✓ /champions/")

# 2. Champion slab pages (all 166)
for name, c in CHAMPS.items():
    write(f'champions/{c["slug"]}/index.html', champion_page(c))
    generated.append(f'/champions/{c["slug"]}/')
print(f"  ✓ {len(CHAMPS)} champion slab pages")

# 3. Counter/matchup pages — each champion vs their top 3 counters
counter_count = 0
for name, c in CHAMPS.items():
    for counter_name in c['counters'][:3]:
        if counter_name in CHAMPS:
            c2 = CHAMPS[counter_name]
            path = f'counters/{c["slug"]}-vs-{c2["slug"]}/index.html'
            write(path, counter_page(c, c2))
            generated.append(f'/counters/{c["slug"]}-vs-{c2["slug"]}/')
            counter_count += 1
print(f"  ✓ {counter_count} counter/matchup pages")

# 4. Role meta guides (5 roles)
for role in ['top', 'jungle', 'mid', 'adc', 'support']:
    path = f'guides/best-{role}-patch-{PATCH.replace(".", "-")}/index.html'
    write(path, meta_guide_page(role))
    generated.append(f'/guides/best-{role}-patch-{PATCH.replace(".", "-")}/')
print("  ✓ 5 role meta guides")

# 5. Guides index
write('guides/index.html', guides_index_page())
generated.append('/guides/')
print("  ✓ /guides/")

# 6. Patch page
write(f'patch/{PATCH.replace(".", "-")}/index.html', patch_page())
generated.append(f'/patch/{PATCH.replace(".", "-")}/')
print(f"  ✓ /patch/{PATCH}/")

# 7. Sitemap
write('sitemap.xml', generate_sitemap(generated))
print("  ✓ sitemap.xml")

# 8. Robots.txt
write('robots.txt', robots_txt())
print("  ✓ robots.txt")

# Count total
total = sum(1 for _ in Path('site').rglob('*.html'))
total += 2  # sitemap + robots
print(f"\n{'='*50}")
print(f"COMPLETE — {total} files generated in ./site/")
print(f"{'='*50}")
print(f"  Champion pages:  {len(CHAMPS)}")
print(f"  Counter pages:   {counter_count}")
print(f"  Meta guides:     5")
print(f"  Patch pages:     1")
print(f"  Index pages:     3 (/champions/, /guides/, /)")
print(f"  sitemap.xml:     {len(generated)} URLs indexed")
print(f"\nTo deploy: follow DEPLOYMENT.md instructions")
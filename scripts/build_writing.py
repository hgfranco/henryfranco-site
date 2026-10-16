"""Build static writing pages from trusted repository Markdown."""
from pathlib import Path
from datetime import date
import html
import json
import re
import markdown
import yaml

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
OUT = SITE / "writing"
OUT.mkdir(exist_ok=True)
home = (SITE / "index.html").read_text()
header = re.search(r'<header class="site-header">.*?</header>', home, re.S).group()
header = header.replace('href="/writing/"', 'href="/writing/" aria-current="page"')
footer = re.search(r'<footer class="site-footer">.*?</footer>', home, re.S).group()
esc = html.escape
posts = []
for source in sorted((ROOT / "content/writing").glob("*.md")):
    parts = source.read_text().split("---", 2)
    if len(parts) != 3 or parts[0].strip():
        raise ValueError(f"{source}: expected YAML front matter")
    meta = yaml.safe_load(parts[1])
    if not isinstance(meta, dict) or not isinstance(meta.get("draft", False), bool):
        raise ValueError(f"{source}: invalid metadata")
    if meta.get("draft", False):
        continue
    for key in ("title", "description", "date", "tags"):
        if key not in meta:
            raise ValueError(f"{source}: missing {key}")
    if not isinstance(meta["tags"], list) or not all(isinstance(t, str) for t in meta["tags"]):
        raise ValueError(f"{source}: tags must be strings")
    day = date.fromisoformat(str(meta["date"]))
    if day > date.today():
        continue
    slug = source.stem
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
        raise ValueError(f"{source}: invalid slug")
    posts.append(dict(meta, slug=slug, day=day, body=parts[2]))
posts.sort(key=lambda p: (p["day"], p["slug"]), reverse=True)

def page(title, description, path, body, kind="website"):
    url = "https://henryfranco.com" + path
    schema = json.dumps({"@context":"https://schema.org", "@type":"Blog" if kind == "website" else "BlogPosting", "name":title, "url":url, "author":{"@type":"Person","name":"Henry Franco"}}).replace("<", "&lt;")
    return f'''<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} | henry franco</title>
<meta name="description" content="{esc(description, quote=True)}">
<link rel="canonical" href="{url}">
<meta property="og:title" content="{esc(title, quote=True)} | henry franco">
<meta property="og:description" content="{esc(description, quote=True)}">
<meta property="og:type" content="{kind}"><meta property="og:url" content="{url}">
<meta name="twitter:card" content="summary"><meta name="theme-color" content="#f7f3e9">
<link rel="stylesheet" href="/styles.css">
<script type="application/ld+json">{schema}</script>
</head><body><a class="skip-link" href="#main">Skip to content</a>
<div class="page">{header}<main id="main">{body}</main>{footer}</div></body></html>'''

entries = []
for index, post in enumerate(posts, 1):
    title, description = esc(post["title"]), esc(post["description"])
    path = "/writing/" + post["slug"] + "/"
    tags = " · ".join(esc(t) for t in post["tags"])
    day = post["day"]
    entries.append(f'''<article class="writing-entry"><span class="project-number">{index:02}</span>
<div class="writing-copy"><h2><a href="{path}">{title}</a></h2><p>{description}</p>
<p class="eyebrow">{tags}</p><a class="text-link" href="{path}">Read <span aria-hidden="true">→</span><span class="visually-hidden"> {title}</span></a></div>
<time datetime="{day.isoformat()}">{day.strftime("%b %Y")}</time></article>''')
    article = f'''<article class="writing-article"><a class="text-link" href="/writing/">← Writing</a>
<header><p class="eyebrow">{tags} · <time datetime="{day.isoformat()}">{day.strftime("%B %Y")}</time></p>
<h1>{title}</h1><p class="intro-text">{description}</p></header>
<div class="article-body">{markdown.markdown(post["body"], extensions=["fenced_code", "tables"])}</div>
<footer class="article-author">Henry Franco<br><span class="section-note">Curious builder</span></footer></article>'''
    directory = OUT / post["slug"]
    directory.mkdir(exist_ok=True)
    (directory / "index.html").write_text(page(post["title"], post["description"], path, article, "article"))
intro = '''<section class="writing-intro"><p class="eyebrow">Writing</p>
<h1>Things I've learned,<br>broken, and <em>figured out.</em></h1>
<p class="intro-text">Notes on Kubernetes, infrastructure, engineering leadership, and whatever I'm currently trying to understand.</p></section>'''
(OUT / "index.html").write_text(page("Writing", "Notes by Henry Franco on Kubernetes, infrastructure, engineering leadership, and learning by building.", "/writing/", intro + '<section class="writing-list" aria-label="Articles">' + "".join(entries) + '</section>'))
paths = ["/", "/about/", "/resume/", "/writing/"] + ["/writing/" + p["slug"] + "/" for p in posts]
(SITE / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + "".join("<url><loc>https://henryfranco.com" + p + "</loc></url>" for p in paths) + "</urlset>\n")
print(f"Built writing index and {len(posts)} articles")

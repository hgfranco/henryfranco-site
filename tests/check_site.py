"""Check the actual container responses, metadata, and linked site assets."""
import json
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

ORIGIN = "http://127.0.0.1:8080"

def get(path):
    return urllib.request.urlopen(ORIGIN + path, timeout=5)

for attempt in range(30):
    try:
        with get("/healthz") as response:
            assert response.read().decode().strip() == "ok"
        break
    except (OSError, AssertionError):
        if attempt == 29:
            raise
        time.sleep(1)

class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.canonical = None
        self.description = None
        self.h1_count = 0
        self.assets = []
        self.collect_schema = False
        self.schema = ""
        self.language = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "html":
            self.language = attrs.get("lang")
        if tag == "h1":
            self.h1_count += 1
        if tag == "meta" and attrs.get("name") == "description":
            self.description = attrs.get("content")
        if tag == "link":
            if attrs.get("rel") == "canonical":
                self.canonical = attrs.get("href")
            if attrs.get("rel") == "stylesheet":
                self.assets.append(attrs["href"])
        if tag == "img" and attrs.get("src", "").startswith("/"):
            self.assets.append(attrs["src"])
        if tag == "script" and attrs.get("type") == "application/ld+json":
            self.collect_schema = True

    def handle_endtag(self, tag):
        if tag == "script":
            self.collect_schema = False

    def handle_data(self, data):
        if self.collect_schema:
            self.schema += data

with get("/") as response:
    html = response.read().decode()
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("Cache-Control") == "no-cache"
page = Page()
page.feed(html)
assert page.language == "en"
assert page.h1_count == 1
assert page.canonical == "https://henryfranco.com/"
assert page.description and "Henry Franco" in page.description
assert "<title>Henry Franco | Engineering Manager</title>" in html
home_schema = json.loads(page.schema)
website_schema = next(item for item in home_schema["@graph"] if item["@type"] == "WebSite")
assert website_schema["name"] == "Henry Franco"
assert website_schema["url"] == "https://henryfranco.com/"
schema = next(item for item in home_schema["@graph"] if item["@type"] == "ProfilePage")
assert schema["@type"] == "ProfilePage"
assert schema["mainEntity"]["name"] == "Henry Franco"
assert schema["mainEntity"]["jobTitle"] == "Engineering Manager"
assert "https://www.instagram.com/hgfranco/" in schema["mainEntity"]["sameAs"]
for asset in page.assets:
    with get(asset) as response:
        assert response.read(), asset
        if asset.startswith("/styles.css"):
            assert response.headers.get("Cache-Control") == "no-cache"
assert 'href="/about/">A little about me' in html
with get("/about/") as response:
    about_html = response.read().decode()
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
about_page = Page()
about_page.feed(about_html)
assert about_page.h1_count == 1
assert about_page.canonical == "https://henryfranco.com/about/"
assert 'aria-current="page"' in about_html
assert 'href="/#projects"' in about_html
assert json.loads(about_page.schema)["mainEntity"]["name"] == "Henry Franco"
for asset in about_page.assets:
    with get(asset) as response:
        assert response.read(), asset
for page_html in (html, about_html):
    assert 'href="/resume/"' in page_html
with get("/resume/") as response:
    resume_html = response.read().decode()
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
resume_page = Page()
resume_page.feed(resume_html)
assert resume_page.h1_count == 1
assert resume_page.canonical == "https://henryfranco.com/resume/"
assert 'href="/resume/" aria-current="page"' in resume_html
assert '<title>Resume | Henry Franco</title>' in resume_html
assert json.loads(resume_page.schema)["mainEntity"]["name"] == "Henry Franco"
for asset in resume_page.assets:
    with get(asset) as response:
        assert response.read(), asset
with get("/robots.txt") as response:
    assert "Sitemap: https://henryfranco.com/sitemap.xml" in response.read().decode()
with get("/sitemap.xml") as response:
    root = ET.fromstring(response.read())
    locations = [item.text for item in root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc")]
    assert locations == ["https://henryfranco.com/", "https://henryfranco.com/about/", "https://henryfranco.com/resume/"]
for missing_path in ("/missing-page", "/missing/nested/page/", "/404.html"):
    try:
        get(missing_path)
    except urllib.error.HTTPError as error:
        assert error.code == 404
        assert error.headers.get("Content-Type", "").startswith("text/html")
        assert error.headers.get("Cache-Control") == "no-cache"
        error_html = error.read().decode()
        assert "<title>Page not found | Henry Franco</title>" in error_html
        assert 'name="robots" content="noindex"' in error_html
        assert 'href="/">Back to home' in error_html
        error_page = Page()
        error_page.feed(error_html)
        assert error_page.h1_count == 1
        for asset in error_page.assets:
            with get(asset) as response:
                assert response.status == 200 and response.read(), asset
    else:
        raise AssertionError("Missing pages must return 404, not the homepage")
print("Website HTTP, metadata, discovery, and asset checks passed.")

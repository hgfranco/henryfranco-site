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
page = Page()
page.feed(html)
assert page.language == "en"
assert page.h1_count == 1
assert page.canonical == "https://henryfranco.dev/"
assert page.description and "Henry Franco" in page.description
assert "<title>Henry Franco | Engineering Manager</title>" in html
schema = json.loads(page.schema)
assert schema["@type"] == "ProfilePage"
assert schema["mainEntity"]["name"] == "Henry Franco"
assert schema["mainEntity"]["jobTitle"] == "Engineering Manager"
assert "https://www.instagram.com/hgfranco/" in schema["mainEntity"]["sameAs"]
for asset in page.assets:
    with get(asset) as response:
        assert response.read(), asset
with get("/robots.txt") as response:
    assert "Sitemap: https://henryfranco.dev/sitemap.xml" in response.read().decode()
with get("/sitemap.xml") as response:
    root = ET.fromstring(response.read())
    locations = [item.text for item in root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc")]
    assert locations == ["https://henryfranco.dev/"]
try:
    get("/missing-page")
except urllib.error.HTTPError as error:
    assert error.code == 404
else:
    raise AssertionError("Missing pages must return 404, not the homepage")
print("Website HTTP, metadata, discovery, and asset checks passed.")

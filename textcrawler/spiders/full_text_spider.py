import scrapy
from urllib.parse import urljoin
import trafilatura
from bs4 import BeautifulSoup

class FullTextSpider(scrapy.Spider):
    name = "full_text"
    handle_httpstatus_all = True

    custom_settings = {
        'ROBOTSTXT_OBEY': False,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 4,
        'DOWNLOAD_DELAY': 0.2,
        'DEFAULT_REQUEST_HEADERS': {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
        },
        'FEED_EXPORT_ENCODING': 'utf-8'
    }

    def __init__(self, start_url=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not start_url:
            raise ValueError("start_url manquant")

        self.start_urls = [start_url]
        self.base_domain = start_url.split("//")[-1].split("/")[0]
        self.visited = set()

    def parse(self, response):
        if response.status != 200:
            return

        soup = BeautifulSoup(response.text, "lxml")

        # ----------------------
        # MÉTA ET STRUCTURE PAGE
        # ----------------------
        title = soup.title.string.strip() if soup.title else ""

        meta_desc_tag = soup.find("meta", attrs={"name": "description"})
        meta_desc = meta_desc_tag["content"].strip() if meta_desc_tag else ""

        h1 = " | ".join([h.get_text(strip=True) for h in soup.find_all("h1")])
        h2 = " | ".join([h.get_text(strip=True) for h in soup.find_all("h2")])
        h3 = " | ".join([h.get_text(strip=True) for h in soup.find_all("h3")])

        paragraphs = " ".join([p.get_text(strip=True) for p in soup.find_all("p")])

        # Récupération texte propre via Trafilatura
        clean_text = trafilatura.extract(response.text) or ""

        # Liens internes
        internal_links = []
        for link in soup.find_all("a", href=True):
            abs_url = urljoin(response.url, link["href"])
            if self.base_domain in abs_url:
                internal_links.append(abs_url)

        # On émet une ligne structurée
        yield {
            "url": response.url,
            "title": title,
            "meta_description": meta_desc,
            "h1": h1,
            "h2": h2,
            "h3": h3,
            "paragraphs": paragraphs,
            "clean_text": clean_text,
            "internal_links": " | ".join(internal_links)
        }

        # ----------------------
        # Lien internes → crawl
        # ----------------------
        for link in internal_links:
            if "#" in link:
                continue
            if link.endswith((".png", ".jpg", ".svg", ".css", ".js")):
                continue
            if link not in self.visited:
                self.visited.add(link)
                yield scrapy.Request(link, callback=self.parse)






# scrapy crawl full_text -a start_url="https://exemple.com" -o site_text.csv
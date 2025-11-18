import scrapy
from urllib.parse import urljoin
import os

class DSpaceFileSpider(scrapy.Spider):
    name = "dspace_files"
    handle_httpstatus_all = True

    custom_settings = {
        'ROBOTSTXT_OBEY': False,
        'REDIRECT_ENABLED': True,
        'HTTPERROR_ALLOWED_CODES': [302, 303, 403],
        'CONCURRENT_REQUESTS': 8,
        'FEED_EXPORT_ENCODING': 'utf-8',
        'DEFAULT_REQUEST_HEADERS': {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
        }
    }

    def __init__(self, start_url=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not start_url:
            raise ValueError("start_url manquant")

        self.start_urls = [start_url]
        self.base_domain = start_url.split("//")[-1].split("/")[0]
        self.visited = set()

        os.makedirs("downloads/pdf", exist_ok=True)

    def parse(self, response):
        if response.status not in [200, 302, 303]:
            return

        for link in response.css("a::attr(href)").getall():
            abs_url = urljoin(response.url, link)

            # Reste dans le domaine
            if self.base_domain not in abs_url:
                continue

            # DSpace PDF detection (les vrais liens de fichiers)
            if "/bitstream/" in abs_url:
                yield scrapy.Request(
                    abs_url,
                    callback=self.save_file,
                    meta={"file_url": abs_url}
                )
                continue

            # Continue à explorer les pages HTML
            if abs_url not in self.visited:
                self.visited.add(abs_url)
                yield scrapy.Request(abs_url, callback=self.parse)

    def save_file(self, response):
        url = response.meta["file_url"]
        filename = url.split("/")[-1].split("?")[0]

        if not filename.lower().endswith(".pdf"):
            filename += ".pdf"

        path = os.path.join("downloads/pdf", filename)

        with open(path, "wb") as f:
            f.write(response.body)

        yield {
            "url": url,
            "filename": filename,
            "relative_path": path
        }

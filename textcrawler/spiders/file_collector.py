import scrapy
from urllib.parse import urljoin
import os

class FileCollectorSpider(scrapy.Spider):
    name = "file_collector"
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

    def __init__(self, start_url=None, extensions=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not start_url:
            raise ValueError("start_url requis")
        if not extensions:
            raise ValueError("extensions requises (ex: pdf,png,jpg)")

        self.start_urls = [start_url]
        self.base_domain = start_url.split("//")[-1].split("/")[0]

        # le chemin racine: /ex /blog /dossier/utile etc.
        self.base_path = "/" + "/".join(start_url.split("/", 3)[3:]) if "/" in start_url[8:] else ""

        # normalisation
        self.base_url_prefix = start_url.rstrip("/")

        self.extensions = [ext.strip().lower() for ext in extensions.split(",")]

        self.visited = set()
        os.makedirs("downloads", exist_ok=True)

    def parse(self, response):
        if response.status != 200:
            return

        for link in response.css("a::attr(href)").getall():
            absolute = urljoin(response.url, link)

            # 1. on vérifie que l'URL reste dans le domaine
            if self.base_domain not in absolute:
                continue

            # 2. on vérifie qu'elle reste dans le chemin demandé (hyper important)
            if not absolute.startswith(self.base_url_prefix):
                continue

            # 3. si c'est un fichier dans les formats recherchés
            if any(absolute.lower().endswith("." + ext) for ext in self.extensions):
                yield scrapy.Request(
                    absolute,
                    callback=self.save_file,
                    meta={"file_url": absolute}
                )
                continue

            # 4. sinon. on continue le crawl dans cette zone uniquement
            if absolute not in self.visited:
                self.visited.add(absolute)
                yield scrapy.Request(absolute, callback=self.parse)

    def save_file(self, response):
        file_url = response.meta["file_url"]
        filename = os.path.basename(file_url)

        ext = filename.split(".")[-1].lower()
        folder = os.path.join("downloads", ext)
        os.makedirs(folder, exist_ok=True)

        file_path = os.path.join(folder, filename)

        with open(file_path, "wb") as f:
            f.write(response.body)

        yield {
            "url": file_url,
            "filename": filename,
            "relative_path": file_path
        }






# lancer : scrapy crawl file_collector -a start_url="https://exemple.com" -a extensions="pdf,png" -o fichiers_collectés.csv

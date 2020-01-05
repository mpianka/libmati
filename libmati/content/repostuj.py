import os

from requests import Response
from requests_html import HTMLSession, HTMLResponse

from libmati.utils.config import sget
from libmati.utils.content import Content, ContentProvider
from libmati.utils.exceptions import ConfigError
from libmati.utils.logging import get_logger

log = get_logger(__name__)


class RepostujContentProvider(ContentProvider):
    PROVIDER_NAME = "Repostuj"
    PROVIDER_URL = "https://repostuj.pl"
    AVAILABLE_CONFIG_VALUES = {
        'base_url': "URL to start searching with. Should be startpage or 'popular' page"
    }

    def __init__(self, provider_id: str, config: dict):
        super().__init__(provider_id, config)
        self.session = HTMLSession()

    @property
    def base_url(self):
        default = "https://repostuj.pl/popularne/"
        conf_value = sget(self.config, "properties.base_url")

        if conf_value:
            log.info("Found `base_url` config value, using it instead of a default one")

            if "repostuj.pl" not in conf_value:
                raise ConfigError(f"Invalid `base_url` key in {self.provider_id} config")

        return conf_value or default

    @property
    def limit(self):
        default = 100
        conf_value = sget(self.config, "limit")

        if conf_value:
            log.info("Found `limit` config value, using it instead of a default one")

        return conf_value or default

    def get_all(self):
        url = self.base_url
        elements = []

        while True:
            response = self.session.get(url)
            url = self._get_next_url(response.html)
            current = self._parse_html(response)

            if elements and (elements[-1].title == current.title and elements[-1] == current.cid):
                break

            if self.limit and len(elements) >= self.limit:
                log.info(f"Hit {self.limit} elements limit")
                break

            log.info(f"Found {current} via {self.__class__.__name__}")
            elements.append(current)

        log.info(f"Found total of {len(elements)} elements")
        return elements

    def get_single(self, url):
        response = self.session.get(url)
        current = self._parse_html(response)

        return current

    def _parse_html(self, resp: Response) -> Content:
        return Content(
            cid=self._get_cid(resp.html),
            mimetype=self._get_mimetype(resp.html),
            title=self._get_title(resp.html),
            description=self._get_description(resp),
            content_url=self._get_url(resp.html),
            base_url=self._get_base_url(resp.html)
        )

    def _get_cid(self, page: HTMLResponse) -> str:
        return os.path.basename(os.path.splitext(self._get_url(page))[0])

    def _get_mimetype(self, page: HTMLResponse) -> str:
        resp = self.session.head(self._get_url(page))
        return resp.headers.get('content-type')

    def _get_title(self, page: HTMLResponse) -> str:
        return page.find('span.title', first=True).text.split(' | ')[1]

    def _get_description(self, page: HTMLResponse) -> str:
        return ""

    def _get_url(self, page: HTMLResponse) -> (str, None):
        img = page.find('img.img-fluid', first=True)
        video = page.find('source')
        url = ""

        if img:
            url = img.attrs.get('src')
        elif video:
            source_tag = [e for e in filter(lambda el: el.attrs.get('type') == "video/mp4", video)]
            if len(source_tag):
                source_tag = source_tag[0]
                url = source_tag.attrs.get('src')

        if not url:
            return None
        else:
            return f"{self.PROVIDER_URL}{url}"

    def _get_base_url(self, resp: Response) -> str:
        return resp.url

    def _get_next_url(self, page: HTMLResponse) -> str:
        return f"{self.PROVIDER_URL}{page.find('#post-prev-btn', first=True).attrs.get('href')}"

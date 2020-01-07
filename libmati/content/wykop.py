from requests_html import HTMLSession
from w3lib.html import remove_tags
from wykop import WykopAPIv2
from youtube_dl.YoutubeDL import YoutubeDL

from libmati.utils.config import sget
from libmati.utils.content import ContentProvider, Content
from libmati.utils.exceptions import ConfigError, ContentError
from libmati.utils.logging import get_logger

log = get_logger(__name__)


class WykopMikroblogContentProvider(ContentProvider):
    PROVIDER_NAME = "Wykop"
    PROVIDER_URL = "https://wykop.pl/mikroblog"
    AVAILABLE_CONFIG_VALUES = {
        'api_key': "API key",
        'api_secret': "API secret key",
        'tag': "Tag to search entries in. If not provided, it will grab entries from hot page",
        'upvotes_gte': "Only get entries where there are >= upvotes"
    }

    def __init__(self, provider_id: str, config: dict):
        super().__init__(provider_id, config)
        self._api = None
        self.session = HTMLSession()

    @property
    def api(self) -> WykopAPIv2:
        if not self._api:
            if 'api_key' not in self.config or 'api_secret' not in self.config:
                raise ConfigError(f"Required api_key or api_secret not found for {self.provider_id}")

            self._api = WykopAPIv2(appkey=self.config.get('api_key'), secretkey=self.config.get('api_secret'))

        return self._api

    def get_all(self):
        entries = []

        # get enough posts for tag (or from hot)
        tag = self.config.get('tag')
        limit = self.config.get('limit') or 50
        upvotes_gte = self.config.get("upvotes_gte") or 0
        hot_entries_period = 6
        page = 1
        while len(entries) < limit:
            current = []
            if tag:
                log.info(f"Calling WykopAPI for page {page} of #{tag} entries...")
                current = self.api.get_tag_entries(tag, page)['data']
            else:
                log.info(f"Calling WykopAPI for page {page} of hot entries (for {hot_entries_period}h period)...")
                current = self.api.get_hot_entries(hot_entries_period, page)['data']

            # check if they have 'embed' field (so they have content) and
            # if they have enough upvotes, so we iterate/filter only once
            current = list(filter(lambda e: e.get('embed') and e.get('vote_count') >= upvotes_gte, current))

            page += 1
            for e in current:
                entries.append(e)

        # get first n elements if the list is too big
        entries = entries[:limit]

        return [self._get_content(e) for e in entries]

    def get_single(self, url):
        entry_id = url.split('/')[-1]
        log.info(f"Calling WykopAPI for single item (#{entry_id})")

        entry = self.api.get_entry(entry_id)

        return self._get_content(entry)

    def _get_content(self, entry):
        # if embed.url is not an internal wykop's link, try to find origin and grab direct link for it
        log.info(f"Found new Content entry from WykopAPI: #{sget(entry, 'cid')}")

        embed_url = sget(entry, 'embed.url')
        content_external = None
        if 'streamable' in embed_url:
            log.info(f"Entry #{sget(entry, 'cid')} is from Streamable, correcting URLs...")

            content_external = entry['embed']['url']
            entry['embed']['url'] = YoutubeDL().extract_info(embed_url, download=False)['url']
        elif 'gfycat' in embed_url:
            log.info(f"Entry #{sget(entry, 'cid')} is from Gfycat, correcting URLs...")

            content_external = entry['embed']['url']
            entry['embed']['url'] = YoutubeDL().extract_info(embed_url, download=False)['url']
        elif 'youtube' in embed_url:
            log.info(f"Entry #{sget(entry, 'cid')} is from YouTube, correcting URLs...")

            content_external = entry['embed']['url']
            entry['embed']['url'] = YoutubeDL().extract_info(embed_url, download=False)['url']
        elif 'wykop' in embed_url:
            log.info(f"Entry #{sget(entry, 'cid')} is internal Wykop\'s content")
            pass
        else:
            log.error(f"Found unsupported content type for entry #{entry['id']}. Check it manually.")
            raise ContentError(f"Unknown content type for #{entry['id']} [{entry['embed']['url']}]")

        return Content(
            cid=sget(entry, 'id'),
            mimetype=self._get_mimetype(sget(entry, 'embed.url')),
            title=sget(entry, 'id'),
            description=remove_tags(sget(entry, 'body')),
            content_url=sget(entry, 'embed.url'),
            base_url=f"https://wykop.pl/wpis/{sget(entry, 'id')}",
            content_external=content_external if content_external else None
        )

    def _get_mimetype(self, url) -> str:
        resp = self.session.head(url)
        return resp.headers.get('content-type')

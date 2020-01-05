class ContentProvider:
    PROVIDER_NAME: str = None
    PROVIDER_URL: str = None
    AVAILABLE_CONFIG_VALUES: dict = None

    def __init__(self, provider_id: str, config: dict):
        assert self.PROVIDER_NAME, "Provider name not provided"
        assert self.PROVIDER_URL, "Provider URL not provided"

        self.provider_id = provider_id
        self.config = config

    def get_all(self):
        raise NotImplementedError

    def get_single(self, url):
        raise NotImplementedError


class Content:
    def __init__(self, cid: str, mimetype: str, title: str, description: str, content_url: str, base_url: str,
                 content_external: str = None, ):
        self.cid = cid
        self.mimetype = mimetype
        self.title = title
        self.description = description
        self.content_url = content_url
        self.base_url = base_url
        self.content_external = content_external

    def __repr__(self):
        return f"<Content type:{self.mimetype}: {self.cid}>"

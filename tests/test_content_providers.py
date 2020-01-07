from unittest import TestCase

from libmati.utils.config import YamlConfig


class TestContentProviders(TestCase):
    def test_get_all(self):
        from libmati.content.repostuj import RepostujContentProvider
        from libmati.content.wykop import WykopMikroblogContentProvider

        config = YamlConfig().config
        providers = [(RepostujContentProvider, 'repostuj'), (WykopMikroblogContentProvider, 'wykop_humorobrazkowy')]

        content = []
        for p in providers:
            cls, prvid = p
            all_items = cls(prvid, config['content_providers'][prvid]['properties']).get_all()
            [content.append(i) for i in all_items]

            assert len(all_items) > 0

        [print(i) for i in content]

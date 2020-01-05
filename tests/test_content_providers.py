from unittest import TestCase


class TestContentProviders(TestCase):
    def test_get_all(self):
        from libmati.content.repostuj import RepostujContentProvider
        from libmati.content.wykop import WykopMikroblogContentProvider

        providers = (RepostujContentProvider, WykopMikroblogContentProvider)
        provider_id = "test"
        config = {'api_key': '9r1sYbA1QU', 'api_secret': '5UBvFucvN9'}
        content = []

        for p in providers:
            all_items = p(provider_id, config).get_all()
            [content.append(i) for i in all_items]

            assert len(all_items) > 0

        [print(i) for i in content]

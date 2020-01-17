from clients import base
from clients.skyeng import schemas


class SkyengClient(base.JSONClient):
    session = base.Session.create_with_retry_policy()
    base_url = 'https://dictionary.skyeng.ru'

    def search_word_meaning(self, word: str, max_words=5) -> schemas.WordList:
        response = self.get(
            'api/public/v1/words/search',
            params={'search': word, 'pageSize': max_words}
        )
        return self.parse_json_response(response, schemas.WordList)

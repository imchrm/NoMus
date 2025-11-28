from typing import Protocol


class VocabularyInterface(Protocol):
    def get_translation(self, text_key: str, lang: str = 'en') -> str:
        ...
    
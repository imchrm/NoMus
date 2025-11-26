# src/nomus/presentation/bot/filters/lexicon_filter.py
from aiogram.filters import BaseFilter
from aiogram.types import Message
from ..lexicon.lexicon import LEXICON

class LexiconFilter(BaseFilter):
    def __init__(self, text_key: str):
        self.text_key = text_key

    async def __call__(self, message: Message) -> bool:
        if not message.text:
            return False
        
        # We get all possible translations for current `text_key`
        possible_translations = [
            lang_dict.get(self.text_key) for lang_dict in LEXICON.values()
        ]
        
        # We check whether the message text matches one of the translations
        return message.text in possible_translations

from aiogram.filters import BaseFilter
from aiogram.types import Message
from nomus.config.settings import Messages


class TextEquals(BaseFilter):
    def __init__(self, field_name: str):
        self.field_name = field_name

    async def __call__(self, message: Message, lexicon: Messages) -> bool:
        if not message.text:
            return False

        expected_text = getattr(lexicon, self.field_name, None)
        return message.text == expected_text

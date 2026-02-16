import re

from aiogram.filters import BaseFilter
from aiogram.types import Message

from nomus.config.settings import Messages

# Pattern: one or more emoji-like characters at the start, followed by optional whitespace.
_EMOJI_PREFIX_RE = re.compile(
    r"^["
    r"\U0001F300-\U0001FAFF"  # Misc Symbols & Pictographs, Emoticons, etc.
    r"\u2600-\u27BF"  # Misc Symbols, Dingbats
    r"\uFE00-\uFE0F"  # Variation Selectors
    r"\u200D"  # Zero Width Joiner
    r"]+\s*"
)


class EmojiPrefixEquals(BaseFilter):
    """
    Matches message text against a localized lexicon field that may have an emoji prefix.

    1. Exact match (normal button press) — always works.
    2. Fallback: strips the leading emoji from the expected text and compares
       (handles the unlikely case when a user types the text without the emoji).
    """

    def __init__(self, field_name: str):
        self.field_name = field_name

    async def __call__(self, message: Message, lexicon: Messages) -> bool:
        if not message.text:
            return False

        expected = getattr(lexicon, self.field_name, None)
        if expected is None:
            return False

        # Exact match (button press)
        if message.text == expected:
            return True

        # Fallback: strip emoji prefix from expected and compare
        stripped = _EMOJI_PREFIX_RE.sub("", expected)
        if stripped and message.text == stripped:
            return True

        return False

# # src/nomus/presentation/bot/lexicon/lexicon.py
# from typing import Dict
# from .ru import LEXICON_RU
# from .en import LEXICON_EN

# # Vocabulary, where key - code of language, value - vocabulary with translations
# LEXICON: dict[str, dict[str, str]] = {
#     'ru': LEXICON_RU,
#     'en': LEXICON_EN,
# }

# def get_translation(text_key: str, lang: str = 'en') -> str:
#     """Returning translation by key for specified language."""
#     return LEXICON.get(lang, LEXICON['ru']).get(text_key, f"_{text_key}_")
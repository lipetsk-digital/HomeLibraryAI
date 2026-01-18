""" Lists of bot commands and user's actions.

Used for building inline keyboards and menus of the bot.
"""

def _translate_(text: str) -> str:
    """ Dummy function for pybabel to detect translatable strings without immediately translating them."""
    return text

MAIN_MENU_ACTIONS = [
    _translate_("add"),
    _translate_("search")
]
ADVANCED_ACTIONS = [
    _translate_("rename"),
    _translate_("export"),
    _translate_("settings")
]
SEARCH_ACTIONS = [
    _translate_("recent"),
    _translate_("cat"),
    _translate_("favorites"),
    _translate_("likes"),
    _translate_("cancel")
]
SEARCH_INTROS = [
    _translate_("recent_intro"),
    _translate_("cat_intro"),
    _translate_("favorites_intro"),
    _translate_("likes_intro"),
    _translate_("text_intro")
]
COVER_ACTIONS = [
    _translate_("use_cover"),
    _translate_("use_original_photo"),
    _translate_("take_new_photo")
]
PUBLIC_BOOK_FIELDS = [
    _translate_("title"),
    _translate_("authors_full_names"),
    _translate_("pages"),
    _translate_("publisher"),
    _translate_("year"),
    _translate_("isbn"),
    _translate_("brief"),
    _translate_("favorites"),
    _translate_("likes")
]
HIDDEN_BOOK_FIELDS = [
    "photo_filename",
    "cover_filename",
    "brief_filename",
    "brief2_filename",
    _translate_("authors"),
    _translate_("annotation"),
    "user_id",
    _translate_("book_id"),
    _translate_("category")
]
BOOK_ACTIONS = [
    _translate_("move_book"),
    _translate_("delete_book"),
    _translate_("save_changes"),
    _translate_("cancel")
]
BOOK_PROMPT = [
    _translate_("prompt_photo"),
    _translate_("prompt_result"),
    _translate_("prompt_count"),
    _translate_("prompt_lang"),
    _translate_("prompt_characters"),
    _translate_("prompt_plaintext"),
    _translate_("prompt_fields"),
    _translate_("prompt_title"),
    _translate_("prompt_authors"),
    _translate_("prompt_pages"),
    _translate_("prompt_publisher"),
    _translate_("prompt_year"),
    _translate_("prompt_isbn"),
    _translate_("prompt_annotation"),
    _translate_("prompt_brief"),
    _translate_("prompt_authors_full_names")
]
BRIEF_ACTIONS = [
    _translate_("use_brief"),
    _translate_("edit_brief"),
    _translate_("favorites"),
    _translate_("likes"),
    _translate_("take_new_photo")
]
NEXT_ACTIONS = [
    _translate_("add_another_book"),
    _translate_("no_another_book")
]
CONFIRM_DELETE = [
    _translate_("delete"),
    _translate_("cancel")
]

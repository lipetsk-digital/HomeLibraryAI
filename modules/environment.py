from modules.imports import StatesGroup, State, CallbackData, eng

# States of conversation with the user for FSM
class State(StatesGroup):
    wait_for_command = State()
    select_lang = State()
    select_cathegory = State()
    wait_for_cover_photo = State()
    wait_reaction_on_cover = State()
    wait_for_brief_photo = State()
    wait_reaction_on_brief = State()
    wait_next_book = State()
    select_field = State()
    wait_for_field_value = State()
    wait_for_search_query = State()
    wait_for_new_cathegory_name = State()

# State data description
  # inline: int - message ID of the last sent message with inline keyboard

# Main menu actions
MAIN_MENU_ACTIONS = [
    eng._translate_("add"),
    eng._translate_("search"),
    eng._translate_("history"),
    eng._translate_("cat")
]
ADVANCED_ACTIONS = [
    eng._translate_("rename"),
    eng._translate_("export"),
    eng._translate_("settings")
]
COVER_ACTIONS = [
    eng._translate_("use_cover"),
    eng._translate_("use_original_photo"),
    eng._translate_("take_new_photo")
]
BOOK_FIELDS = [
    eng._translate_("title"),
    eng._translate_("authors_full_names"),
    eng._translate_("pages"),
    eng._translate_("publisher"),
    eng._translate_("year"),
    eng._translate_("isbn"),
    eng._translate_("brief")
]
ADVANCED_BOOK_FIELDS = [
    "user_id",
    "book_id",
    eng._translate_("cathegory"),
    "photo_filename",
    "cover_filename",
    "brief_filename",
    eng._translate_("authors"),
    eng._translate_("annotation")
]
BOOK_PROMPT = [
    eng._translate_("prompt_photo"),
    eng._translate_("prompt_result"),
    eng._translate_("prompt_count"),
    eng._translate_("prompt_lang"),
    eng._translate_("prompt_characters"),
    eng._translate_("prompt_plaintext"),
    eng._translate_("prompt_fields"),
    eng._translate_("prompt_title"),
    eng._translate_("prompt_authors"),
    eng._translate_("prompt_pages"),
    eng._translate_("prompt_publisher"),
    eng._translate_("prompt_year"),
    eng._translate_("prompt_isbn"),
    eng._translate_("prompt_annotation"),
    eng._translate_("prompt_brief"),
    eng._translate_("prompt_authors_full_names")
]
BRIEF_ACTIONS = [
    eng._translate_("use_brief"),
    eng._translate_("edit_brief"),
    eng._translate_("take_new_photo")
]
NEXT_ACTIONS = [
    eng._translate_("add_another_book"),
    eng._translate_("no_another_book")
]

# Callback factory for main menu
class MainMenu(CallbackData, prefix="main"):
    action: str

# Callback factory for cathegory selection
class Cathegory(CallbackData, prefix="cat"):
    name: str

# Callback factory for language selection
class Language(CallbackData, prefix="lang"):
    lang: str

# Callback factory for cover actions
class CoverActions(CallbackData, prefix="cover"):
    action: str

# Callback factory for the annotation page actions
class BriefActions(CallbackData, prefix="brief"):
    action: str

# Callback factory for the next actions
class NextActions(CallbackData, prefix="next"):
    action: str

# Callback factory for the book fields
class BookFields(CallbackData, prefix="field"):
    field: str

# Callback factory for editing book
class EditBook(CallbackData, prefix="edit"):
    book_id: int


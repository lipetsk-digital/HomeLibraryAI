from modules.imports import CallbackData, StatesGroup, State

# -------------------------------------------------------
# Finite State Machine
# -------------------------------------------------------

# States of conversation with the user
class State(StatesGroup):
    wait_for_command = State()
    select_lang = State()
    select_category = State()
    wait_for_cover_photo = State()
    wait_reaction_on_cover = State()
    wait_for_brief_photo = State()
    wait_reaction_on_brief = State()
    wait_next_book = State()
    select_field = State()
    wait_for_field_value = State()
    wait_for_search_query = State()
    wait_for_new_category_name = State()

# States data description of users conversation
    # inline: int - message ID of the last sent message with inline keyboard
    # action: str - global action being performed: 
    #             ["add_book", "select_category", "rename_category"]
    # category: str - selected category name
    #
    # photo_filename: str - filename of the uploaded book cover photo
    # cover_filename: str - filename of the processed book cover photo
    # brief_filename: str - filename of the uploaded brief photo
    # title: str - book title
    # authors: str - original string of book authors
    # authors_full_names: str - full names of the book authors
    # pages: str - number of pages in the book
    # publisher: str - book publisher
    # year: str - publication year
    # isbn: str - ISBN number
    # annotation: str - full book annotation
    # brief: str - brief description of the book
    # book_id: int - ID of the book being processed
    #
    # field: str - currently selected book field for editing


# -------------------------------------------------------
# Lists of commands and fields
# -------------------------------------------------------

# Dummy function for pybabel to detect translatable strings
def _translate_(text: str) -> str:
    return text

# Main menu actions
MAIN_MENU_ACTIONS = [
    _translate_("add"),
    _translate_("search"),
    _translate_("history"),
    _translate_("cat")
]
ADVANCED_ACTIONS = [
    _translate_("rename"),
    _translate_("export"),
    _translate_("settings")
]
COVER_ACTIONS = [
    _translate_("use_cover"),
    _translate_("use_original_photo"),
    _translate_("take_new_photo")
]
BOOK_FIELDS = [
    _translate_("title"),
    _translate_("authors_full_names"),
    _translate_("pages"),
    _translate_("publisher"),
    _translate_("year"),
    _translate_("isbn"),
    _translate_("brief")
]
ADVANCED_BOOK_FIELDS = [
    "photo_filename",
    "cover_filename",
    "brief_filename",
    _translate_("authors"),
    _translate_("annotation")
]
SPECIAL_BOOK_FIELDS = [
    "user_id",
    "book_id",
    _translate_("category")
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
    _translate_("take_new_photo")
]
NEXT_ACTIONS = [
    _translate_("add_another_book"),
    _translate_("no_another_book")
]

# -------------------------------------------------------
# Callback data factories
# -------------------------------------------------------

# Callback factory for main menu
class MainMenu(CallbackData, prefix="main"):
    action: str

# Callback factory for category selection
class Category(CallbackData, prefix="cat"):
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


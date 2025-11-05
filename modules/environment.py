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
    wait_for_brief_photo1of1 = State()
    wait_for_brief_photo1of2 = State()
    wait_for_brief_photo2of2 = State()
    wait_reaction_on_brief = State()
    wait_next_book = State()
    select_field = State()
    wait_for_field_value = State()
    wait_for_search_query = State()
    wait_for_new_category_name = State()
    confirm_delete_book = State()

# States data description of users conversation
    # Data of user conversation:
    # -------------------------------------------------------
    # inline: int - message ID of the last sent message with inline keyboard
    # action: str - global action being performed: 
    #             [ "add_book", "search", "rename_category", "edit_book", "select_language" ]
    # category: str - selected category name
    # field: str - currently selected book field for editing
    # brief_base64: str - base64 of the uploaded brief photo
    # brief2_base64: str - base64 of the uploaded brief photo
    #
    # Data of the book fields:
    # -------------------------------------------------------
    # photo_filename: str - filename of the uploaded book cover photo
    # cover_filename: str - filename of the processed book cover photo
    # brief_filename: str - filename of the uploaded brief photo
    # brief2_filename: str - filename of the uploaded brief photo
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
    # favorites: bool - is the book marked as favorite
    # likes: bool - is the book marked as liked



# -------------------------------------------------------
# Lists of commands and fields
# -------------------------------------------------------

# Dummy function for pybabel to detect translatable strings
def _translate_(text: str) -> str:
    return text

# Main menu actions
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

# -------------------------------------------------------
# Callback data factories
# -------------------------------------------------------

# Callback factory for main menu
class MainMenu(CallbackData, prefix="main"):
    action: str

# Callback factory for search menu
class SearchMenu(CallbackData, prefix="search"):
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

# Callback factory for confirming deletion
class ConfirmDelete(CallbackData, prefix="confirm"):
    action: str

# Callback factory for take two brief photos
class BriefPhotos(CallbackData, prefix="photos"):
    count: int
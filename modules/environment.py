import modules.engine as eng

# Finite State Machine

# -------------------------------------------------------
# States of conversation with the user
# -------------------------------------------------------

class State(eng.StatesGroup):
    wait_for_command = eng.State()
    select_lang = eng.State()
    select_category = eng.State()
    wait_for_cover_photo = eng.State()
    wait_reaction_on_cover = eng.State()
    wait_for_brief_photo1of1 = eng.State()
    wait_for_brief_photo1of2 = eng.State()
    wait_for_brief_photo2of2 = eng.State()
    wait_reaction_on_brief = eng.State()
    wait_next_book = eng.State()
    select_field = eng.State()
    wait_for_field_value = eng.State()
    wait_for_search_query = eng.State()
    wait_for_new_category_name = eng.State()
    confirm_delete_book = eng.State()

# -------------------------------------------------------
# Data description of users conversation
# -------------------------------------------------------

# Internal data fields:
# -------------------------------------------------------
# messages_to_remove: list[int] - ID of messages to remove them after an user reaction
# keyboards_to_remove: list[int] - ID of messages with inline keyboards to remove the keyboards after an user reaction

# Data of user conversation:
# -------------------------------------------------------
# action: str - global action being performed: 
#             [ "add_book", "search", "rename_category", "edit_book", "select_language" ]
# category: str - selected category name
# field: str - currently selected book field for editing
# brief_base64: str - base64 of the uploaded brief photo
# brief2_base64: str - base64 of the uploaded brief photo
# photo_token: str - messenger token of the user's uploaded book cover photo

# Data of the book fields:
# -------------------------------------------------------
# photo_filename: str - filename of the uploaded book cover photo
# cover_filename: str - filename of the processed book cover photo
# cover_token: str - messenger token of the processed book cover photo
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
# Callback data factories
# -------------------------------------------------------

# Callback factory for main menu
class MainMenu(eng.CallbackData(), prefix="main"):
    action: str

# Callback factory for search menu
class SearchMenu(eng.CallbackData(), prefix="search"):
    action: str

# Callback factory for category selection
class Category(eng.CallbackData(), prefix="cat"):
    name: str

# Callback factory for language selection
class Language(eng.CallbackData(), prefix="lang"):
    lang: str

# Callback factory for cover actions
class CoverActions(eng.CallbackData(), prefix="cover"):
    action: str

# Callback factory for the annotation page actions
class BriefActions(eng.CallbackData(), prefix="brief"):
    action: str

# Callback factory for the next actions
class NextActions(eng.CallbackData(), prefix="next"):
    action: str

# Callback factory for the book fields
class BookFields(eng.CallbackData(), prefix="field"):
    field: str

# Callback factory for editing book
class EditBook(eng.CallbackData(), prefix="edit"):
    book_id: int

# Callback factory for confirming deletion
class ConfirmDelete(eng.CallbackData(), prefix="confirm"):
    action: str

# Callback factory for take two brief photos
class BriefPhotos(eng.CallbackData(), prefix="photos"):
    count: int

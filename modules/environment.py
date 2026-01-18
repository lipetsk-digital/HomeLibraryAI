from modules.imports_tg import CallbackData, StatesGroup, State

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
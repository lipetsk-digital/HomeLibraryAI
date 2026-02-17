import modules.engine as eng

# Finite State Machine

# -------------------------------------------------------
# States of conversation with the user
# -------------------------------------------------------

class State(eng.StatesGroup()):
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
# inline: int - message ID of the last sent message with inline keyboard

# Data of user conversation:
# -------------------------------------------------------
# action: str - global action being performed: 
#             [ "add_book", "search", "rename_category", "edit_book", "select_language" ]
# category: str - selected category name
# field: str - currently selected book field for editing
# brief_base64: str - base64 of the uploaded brief photo
# brief2_base64: str - base64 of the uploaded brief photo

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
class MainMenu(eng.CallbackData(), prefix="main"):
    action: str

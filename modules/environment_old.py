from modules.imports_tg import CallbackData, StatesGroup, State






# -------------------------------------------------------
# Callback data factories
# -------------------------------------------------------

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
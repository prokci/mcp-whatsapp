
from src.mcp_whatsapp.utils.patern_classes import Singleton

languages = ["ru", "en"]

lang_dict = {
    "load_whatsapp_key_word": ["Все", "All"],
    "placeholder_search": ["Поиск или новый чат","Search or start a new chat"],
    "attach": ["Прикрепить","Attach"],
    "document": ["Документ","Document"],
    "close" : ["Закрыть","Close"],
    "discard" : ["Сбросить","Discard"],
}

class Language(Singleton):
    def init(self, lang="ru"):
        self.lang = languages.index(lang)
        
    def __getitem__(self, key):
        return lang_dict[key][self.lang]
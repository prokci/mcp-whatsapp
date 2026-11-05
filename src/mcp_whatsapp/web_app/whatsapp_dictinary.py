
from typing import Final

from src.mcp_whatsapp.utils.patern_classes import Singleton


class Language(Singleton):
    lang_dict:Final = {
        "load_whatsapp_key_word": ["Все", "All"],
        "placeholder_search": ["Поиск или новый чат","Search or start a new chat"],
        "attach": ["Прикрепить","Attach"],
        "document": ["Документ","Document"],
        "close" : ["Закрыть","Close"],
        "discard" : ["Сбросить","Discard"],
    }
    
    languages:Final = ["ru", "en"]
    
    def init(self, lang="ru"):
        self.lang = self.languages.index(lang)
        
    def __getitem__(self, key):
        return self.lang_dict[key][self.lang]
    
    @classmethod
    def get_all_languages(cls, key):
        yield from zip(cls.languages, cls.lang_dict[key])
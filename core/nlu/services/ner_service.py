from typing import List, Dict
from core.nlu.models.ner_model import NERModel


class NERService:
    def __init__(self, model_path: str = None):
        self.ner_model = None
        try:
            self.ner_model = NERModel(model_path)
        except Exception as e:
            print(f"Failed to load NER model: {e}")
    
    def extract_entities(self, text: str) -> List[Dict[str, str]]:
        if self.ner_model:
            return self.ner_model.predict(text)
        else:
            return [{"token": word, "tag": "O"} for word in text.split()]
    
    def is_model_loaded(self) -> bool:
        return self.ner_model is not None